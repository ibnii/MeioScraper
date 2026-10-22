from __future__ import annotations

import argparse
import threading
import time
import webbrowser
from pathlib import Path
from typing import Optional

from flask import (
    Flask,
    Response,
    abort,
    jsonify,
    render_template,
    request,
    send_file,
    stream_with_context,
)

from ..http import HttpClient, HttpError
from ..models import Chapter, Novel
from ..parser import parse_chapter
from ..scraper import MeionovelsScraper, normalize_chapter_url, normalize_novel_url
from .events import iter_events
from .jobs import BusyError, DownloadRequest, JobManager

FORMATS = {"epub", "txt", "json"}
MIMETYPES = {
    "epub": "application/epub+zip",
    "txt": "text/plain; charset=utf-8",
    "json": "application/json",
}


def _default_scraper() -> MeionovelsScraper:
    return MeionovelsScraper(client=HttpClient(delay=1.0))


def _asset_version(static_folder: str) -> str:
    root = Path(static_folder)
    try:
        latest = max(path.stat().st_mtime for path in root.rglob("*") if path.is_file())
    except (OSError, ValueError):
        return "1"
    return str(int(latest))


_READ_LOCK = threading.Lock()
_READ_LAST = [0.0]


def _default_chapter_loader(url: str, cookie: Optional[str]):
    with _READ_LOCK:
        wait = 0.8 - (time.monotonic() - _READ_LAST[0])
        if wait > 0:
            time.sleep(wait)
        try:
            client = HttpClient(delay=0.0, cookie=cookie)
            response = client.get(url)
        finally:
            _READ_LAST[0] = time.monotonic()
    return parse_chapter(response.text, Chapter(index=0, title="", url=url))


def create_app(
    job_manager: Optional[JobManager] = None,
    scraper_factory=None,
    chapter_loader=None,
) -> Flask:
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    app.jinja_env.auto_reload = True

    manager = job_manager or JobManager()
    app.extensions["job_manager"] = manager
    app.extensions["scraper_factory"] = scraper_factory or _default_scraper
    app.extensions["chapter_loader"] = chapter_loader or _default_chapter_loader

    @app.context_processor
    def inject_asset_version():
        return {"asset_version": _asset_version(app.static_folder)}

    @app.after_request
    def no_store_html(response):
        if response.mimetype == "text/html" or request.path.startswith("/static/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/read/<slug>/<int:index>")
    def reader(slug: str, index: int):
        try:
            novel_url = normalize_novel_url(slug)
        except ValueError:
            abort(404)
        if index < 1:
            abort(404)
        return render_template(
            "reader.html",
            reader_config={
                "slug": slug,
                "novel_url": novel_url,
                "index": index,
            },
        )

    @app.get("/api/novel")
    def novel_detail():
        url = (request.args.get("url") or "").strip()
        if not url:
            return _error("URL novel wajib diisi.", 400)

        try:
            scraper = app.extensions["scraper_factory"]()
            novel = scraper.fetch_novel(url)
            chapters = scraper.fetch_chapters(novel)
        except HttpError as exc:
            return _error(str(exc), 502)
        except ValueError as exc:
            return _error(str(exc), 400)

        return jsonify(
            {
                "novel": _novel_payload(novel),
                "chapters": [_chapter_payload(chapter) for chapter in chapters],
                "stats": _stats(chapters),
            }
        )

    @app.post("/api/chapter")
    def chapter_content():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return _error("Payload JSON tidak valid.", 400)

        try:
            url = normalize_chapter_url(str(data.get("url") or ""))
        except ValueError as exc:
            return _error(str(exc), 400)

        cookie = data.get("cookie")
        if not isinstance(cookie, str) or not cookie.strip():
            cookie = None
        else:
            cookie = cookie.strip()[:4096]

        try:
            content = app.extensions["chapter_loader"](url, cookie)
        except HttpError as exc:
            return _error(str(exc), 502)
        except ValueError as exc:
            return _error(str(exc), 502)

        return jsonify(
            {
                "url": url,
                "title": content.title,
                "html": content.html,
                "text": content.text,
                "locked": content.locked,
                "gate_message": content.gate_message,
            }
        )

    @app.post("/api/jobs")
    def create_job():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return _error("Payload JSON tidak valid.", 400)

        try:
            url = normalize_novel_url(str(data.get("url") or ""))
        except ValueError as exc:
            return _error(str(exc), 400)

        raw_chapters = data.get("chapters")
        if not isinstance(raw_chapters, list) or not raw_chapters:
            return _error("Pilih minimal satu chapter.", 400)
        try:
            chapters = sorted({int(value) for value in raw_chapters})
        except (TypeError, ValueError):
            return _error("Daftar chapter tidak valid.", 400)
        if any(value < 1 for value in chapters):
            return _error("Nomor chapter tidak valid.", 400)
        if len(chapters) > 5000:
            return _error("Maksimal 5000 chapter per unduhan.", 400)

        output_format = str(data.get("format") or "epub").lower()
        if output_format not in FORMATS:
            return _error("Format harus epub, txt, atau json.", 400)

        try:
            delay = float(data.get("delay", 1.0))
        except (TypeError, ValueError):
            delay = 1.0
        delay = min(10.0, max(0.25, delay))

        cookie = data.get("cookie")
        if not isinstance(cookie, str) or not cookie.strip():
            cookie = None
        else:
            cookie = cookie.strip()[:4096]

        download_request = DownloadRequest(
            url=url,
            chapters=chapters,
            format=output_format,
            include_cover=bool(data.get("include_cover", True)),
            cookie=cookie,
            delay=delay,
        )

        try:
            job = manager.create(download_request)
        except BusyError as exc:
            return _error(str(exc), 409)

        return jsonify({"job_id": job.id}), 202

    @app.get("/api/jobs/<job_id>/events")
    def job_events(job_id: str):
        job = manager.get(job_id)
        if job is None:
            return _error("Job tidak ditemukan.", 404)

        return Response(
            stream_with_context(iter_events(job)),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
                "Connection": "keep-alive",
            },
        )

    @app.post("/api/jobs/<job_id>/cancel")
    def cancel_job(job_id: str):
        job = manager.get(job_id)
        if job is None:
            return _error("Job tidak ditemukan.", 404)
        job.cancel_event.set()
        return jsonify({"cancelling": True})

    @app.get("/api/jobs/<job_id>/download")
    def download_job(job_id: str):
        job = manager.get(job_id)
        if job is None:
            return _error("Job tidak ditemukan.", 404)
        if job.output is None or not job.output.exists():
            return _error("Berkas belum siap.", 409)

        return send_file(
            job.output,
            as_attachment=True,
            download_name=job.filename or job.output.name,
            mimetype=MIMETYPES.get(job.output.suffix.lstrip("."), "application/octet-stream"),
        )

    @app.errorhandler(404)
    def not_found(_error_value):
        if request.path.startswith("/api/"):
            return _error("Endpoint tidak ditemukan.", 404)
        return render_template("index.html"), 404

    return app


def _novel_payload(novel: Novel) -> dict:
    return {
        "url": novel.url,
        "slug": novel.slug,
        "title": novel.title,
        "alternative_title": novel.alternative_title,
        "author": novel.author,
        "artist": novel.artist,
        "genres": novel.genres,
        "status": novel.status,
        "release": novel.release,
        "cover_url": novel.cover_url,
        "synopsis": novel.synopsis,
    }


def _chapter_payload(chapter: Chapter) -> dict:
    return {
        "index": chapter.index,
        "title": chapter.title,
        "url": chapter.url,
        "locked": chapter.locked,
        "price_label": chapter.price_label,
        "release_date": chapter.release_date,
    }


def _stats(chapters) -> dict:
    locked = sum(1 for chapter in chapters if chapter.locked)
    return {
        "total": len(chapters),
        "free": len(chapters) - locked,
        "locked": locked,
    }


def _error(message: str, status: int):
    return jsonify({"error": message}), status


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="novelin-web",
        description="Antarmuka web lokal untuk Novelin",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args(argv)

    app = create_app()
    url = f"http://{args.host}:{args.port}/"
    print(f"Novelin berjalan di {url}")
    if not args.no_browser:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()

    app.run(host=args.host, port=args.port, threaded=True, debug=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
