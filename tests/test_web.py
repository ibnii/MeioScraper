import time

import pytest

from novelin.http import HttpError
from novelin.models import Chapter, ChapterContent, Novel
from novelin.web import jobs as jobs_module
from novelin.web.app import create_app
from novelin.web.events import iter_events
from novelin.web.jobs import BusyError, DownloadRequest, Job, JobManager


class FakeScraper:
    def __init__(self, client=None):
        self.client = client

    def fetch_novel(self, url):
        return Novel(
            url="https://meionovels.com/novel/novel-uji/",
            slug="novel-uji",
            title="Novel Uji",
            author="Penulis Uji",
        )

    def fetch_chapters(self, novel):
        return [
            Chapter(index=1, title="Chapter 1", url="https://example.test/1"),
            Chapter(index=2, title="Chapter 2", url="https://example.test/2", locked=True),
        ]


class FailingScraper(FakeScraper):
    def fetch_novel(self, url):
        raise HttpError("Situs sedang sibuk.", status=503, url=url)


class StubManager:
    def __init__(self):
        self.request = None
        self.busy = False

    def create(self, request):
        if self.busy:
            raise BusyError("Masih ada unduhan yang berjalan.")
        self.request = request
        return Job(id="job-123")

    def get(self, job_id):
        return None


def _client(scraper_factory=FakeScraper, manager=None, chapter_loader=None):
    app = create_app(
        job_manager=manager,
        scraper_factory=scraper_factory,
        chapter_loader=chapter_loader,
    )
    app.config.update(TESTING=True)
    return app.test_client()


def _chapter_content(locked=False):
    return ChapterContent(
        chapter=Chapter(index=1, title="Chapter 1", url="https://example.test/1"),
        title="Chapter 1",
        html="" if locked else "<p>Isi chapter.</p>",
        text="" if locked else "Isi chapter.",
        locked=locked,
        gate_message="Chapter terkunci" if locked else None,
    )


def test_chapter_endpoint_returns_readable_content():
    loader = lambda url, cookie: _chapter_content()
    response = _client(chapter_loader=loader).post(
        "/api/chapter",
        json={"url": "https://meionovels.com/novel/novel-uji/htl/chapter-1/"},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["title"] == "Chapter 1"
    assert payload["html"] == "<p>Isi chapter.</p>"
    assert payload["locked"] is False


def test_chapter_endpoint_returns_locked_payload():
    loader = lambda url, cookie: _chapter_content(locked=True)
    response = _client(chapter_loader=loader).post(
        "/api/chapter",
        json={"url": "https://meionovels.com/novel/novel-uji/htl/chapter-1/"},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["locked"] is True
    assert payload["gate_message"] == "Chapter terkunci"


@pytest.mark.parametrize(
    "url",
    [
        "",
        "https://example.com/novel/novel-uji/chapter-1/",
        "https://meionovels.com/novel/novel-uji/",
        "javascript:alert(1)",
    ],
)
def test_chapter_endpoint_rejects_invalid_urls(url):
    response = _client().post("/api/chapter", json={"url": url})
    assert response.status_code == 400


def test_chapter_endpoint_maps_loader_error_to_502():
    def failing_loader(url, cookie):
        raise HttpError("Gagal mengambil chapter.", status=503, url=url)

    response = _client(chapter_loader=failing_loader).post(
        "/api/chapter",
        json={"url": "https://meionovels.com/novel/novel-uji/htl/chapter-1/"},
    )
    assert response.status_code == 502


def test_index_serves_page():
    response = _client().get("/")
    assert response.status_code == 200
    assert "Novelin" in response.get_data(as_text=True)


def test_novel_endpoint_returns_metadata_and_stats():
    response = _client().get("/api/novel?url=novel-uji")
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["novel"]["title"] == "Novel Uji"
    assert payload["stats"] == {"total": 2, "free": 1, "locked": 1}
    assert payload["chapters"][1]["locked"] is True


def test_novel_endpoint_requires_url():
    response = _client().get("/api/novel")
    assert response.status_code == 400
    assert "wajib" in response.get_json()["error"]


def test_novel_endpoint_maps_upstream_error():
    response = _client(scraper_factory=FailingScraper).get("/api/novel?url=novel-uji")
    assert response.status_code == 502
    assert "sibuk" in response.get_json()["error"]


@pytest.mark.parametrize(
    "payload",
    [
        {"url": "novel-uji"},
        {"url": "novel-uji", "chapters": []},
        {"url": "novel-uji", "chapters": ["x"]},
        {"url": "https://example.com/novel/novel-uji/", "chapters": [1]},
        {"url": "novel-uji", "chapters": [1], "format": "pdf"},
    ],
)
def test_create_job_rejects_invalid_payloads(payload):
    response = _client().post("/api/jobs", json=payload)
    assert response.status_code == 400


def test_create_job_accepts_valid_payload():
    manager = StubManager()
    response = _client(manager=manager).post(
        "/api/jobs",
        json={
            "url": "novel-uji",
            "chapters": [3, 1, 2],
            "format": "epub",
            "include_cover": False,
            "delay": 2,
            "cookie": "session=abc",
        },
    )

    assert response.status_code == 202
    assert response.get_json() == {"job_id": "job-123"}
    assert manager.request.url == "https://meionovels.com/novel/novel-uji/"
    assert manager.request.chapters == [1, 2, 3]
    assert manager.request.format == "epub"
    assert manager.request.include_cover is False
    assert manager.request.delay == 2.0
    assert manager.request.cookie == "session=abc"


def test_create_job_returns_conflict_when_busy():
    manager = StubManager()
    manager.busy = True
    response = _client(manager=manager).post(
        "/api/jobs",
        json={"url": "novel-uji", "chapters": [1]},
    )
    assert response.status_code == 409


def test_download_requires_ready_file():
    manager = StubManager()
    app = create_app(job_manager=manager, scraper_factory=FakeScraper)
    app.config.update(TESTING=True)

    manager.get = lambda job_id: Job(id=job_id)
    response = app.test_client().get("/api/jobs/job-123/download")
    assert response.status_code == 409


def test_iter_events_emits_terminal_stream():
    job = Job(id="job-1")
    job.emit({"type": "start", "total": 1})
    job.emit({"type": "done", "downloaded": 1})
    job.finish("done")

    stream = "".join(iter_events(job))
    assert '"type": "start"' in stream
    assert '"type": "done"' in stream


def _wait_for_job(job, timeout=5.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if job.status in ("done", "error"):
            return
        time.sleep(0.02)
    raise AssertionError("job did not finish")


def test_worker_downloads_free_and_skips_locked(monkeypatch, tmp_path):
    class FakeClient:
        def __init__(self, delay=1.0, cookie=None):
            self.has_cookie = bool(cookie)

    class WorkerScraper(FakeScraper):
        def fetch_chapter(self, chapter):
            return ChapterContent(
                chapter=chapter,
                title=chapter.title,
                html="<p>Isi.</p>",
                text="Isi.",
            )

    def fake_export(novel, contents, path):
        path.write_text("hasil", encoding="utf-8")
        return path

    monkeypatch.setattr(jobs_module, "HttpClient", FakeClient)
    monkeypatch.setattr(jobs_module, "MeionovelsScraper", WorkerScraper)
    monkeypatch.setattr(jobs_module, "export_txt", fake_export)

    manager = JobManager()
    job = manager.create(
        DownloadRequest(
            url="https://meionovels.com/novel/novel-uji/",
            chapters=[1, 2],
            format="txt",
            delay=0,
        )
    )
    _wait_for_job(job)

    assert job.status == "done"
    assert job.output is not None and job.output.exists()
    done = [event for event in job.events if event["type"] == "done"][-1]
    assert done["downloaded"] == 1
    assert done["skipped"] == 1


def test_worker_reports_all_locked_as_done(monkeypatch):
    class FakeClient:
        def __init__(self, delay=1.0, cookie=None):
            self.has_cookie = False

    monkeypatch.setattr(jobs_module, "HttpClient", FakeClient)
    monkeypatch.setattr(jobs_module, "MeionovelsScraper", FakeScraper)

    manager = JobManager()
    job = manager.create(
        DownloadRequest(
            url="https://meionovels.com/novel/novel-uji/",
            chapters=[2],
            format="txt",
            delay=0,
        )
    )
    _wait_for_job(job)

    assert job.status == "done"
    done = [event for event in job.events if event["type"] == "done"][-1]
    assert done["downloaded"] == 0
    assert done["skipped"] == 1
    assert "terkunci" in done["message"]
