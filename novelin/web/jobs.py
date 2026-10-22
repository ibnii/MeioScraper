from __future__ import annotations

import shutil
import tempfile
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional

from ..exporters import export_epub, export_json, export_txt
from ..http import HttpClient, HttpError
from ..scraper import MeionovelsScraper
from ..utils import safe_filename
from .payloads import chapter_event


class BusyError(RuntimeError):
    pass


@dataclass
class DownloadRequest:
    url: str
    chapters: List[int]
    format: str = "epub"
    include_cover: bool = True
    cookie: Optional[str] = None
    delay: float = 1.0


@dataclass
class Job:
    id: str
    events: List[dict] = field(default_factory=list)
    condition: threading.Condition = field(default_factory=threading.Condition)
    cancel_event: threading.Event = field(default_factory=threading.Event)
    status: str = "queued"
    created: float = field(default_factory=time.time)
    directory: Optional[Path] = None
    output: Optional[Path] = None
    filename: Optional[str] = None
    error: Optional[str] = None

    def mark_running(self) -> None:
        with self.condition:
            self.status = "running"
            self.condition.notify_all()

    def emit(self, event: dict) -> None:
        with self.condition:
            self.events.append(event)
            self.condition.notify_all()

    def finish(self, status: str) -> None:
        with self.condition:
            self.status = status
            self.condition.notify_all()


class JobManager:
    def __init__(
        self,
        max_age: float = 2 * 60 * 60,
        worker: Optional[Callable[[Job, DownloadRequest], None]] = None,
    ) -> None:
        self.max_age = max_age
        self._jobs: Dict[str, Job] = {}
        self._lock = threading.Lock()
        self._worker = worker or self._run

    def create(self, request: DownloadRequest) -> Job:
        self.cleanup()
        with self._lock:
            if any(
                job.status in ("queued", "running") for job in self._jobs.values()
            ):
                raise BusyError("Masih ada unduhan yang berjalan.")
            job = Job(id=uuid.uuid4().hex[:12])
            self._jobs[job.id] = job

        thread = threading.Thread(
            target=self._worker,
            args=(job, request),
            daemon=True,
        )
        thread.start()
        return job

    def get(self, job_id: str) -> Optional[Job]:
        with self._lock:
            return self._jobs.get(job_id)

    def cleanup(self) -> None:
        cutoff = time.time() - self.max_age
        with self._lock:
            stale = [
                job_id
                for job_id, job in self._jobs.items()
                if job.created < cutoff and job.status not in ("queued", "running")
            ]
            for job_id in stale:
                job = self._jobs.pop(job_id)
                if job.directory is not None:
                    shutil.rmtree(job.directory, ignore_errors=True)

    def _run(self, job: Job, request: DownloadRequest) -> None:
        job.mark_running()
        job.emit({"type": "stage", "stage": "setup", "message": "Menyiapkan unduhan..."})

        try:
            client = HttpClient(delay=request.delay, cookie=request.cookie)
            scraper = MeionovelsScraper(client=client)

            job.emit(
                {"type": "stage", "stage": "novel", "message": "Mengambil detail novel..."}
            )
            novel = scraper.fetch_novel(request.url)

            job.emit(
                {
                    "type": "stage",
                    "stage": "chapters",
                    "message": "Mengambil daftar chapter...",
                }
            )
            chapters = scraper.fetch_chapters(novel)
            wanted = set(request.chapters)
            selected = [chapter for chapter in chapters if chapter.index in wanted]
            if not selected:
                raise ValueError("Chapter yang dipilih tidak ditemukan.")

            total = len(selected)
            job.emit({"type": "start", "title": novel.title, "total": total})

            contents = []
            downloaded = 0
            skipped = 0
            failed = 0
            cancelled = False

            for chapter in selected:
                if job.cancel_event.is_set():
                    cancelled = True
                    break

                if chapter.locked and not client.has_cookie:
                    skipped += 1
                    job.emit(
                        chapter_event(
                            chapter,
                            "skipped",
                            downloaded,
                            skipped,
                            failed,
                            total,
                            "Terkunci, dilewati",
                        )
                    )
                    continue

                job.emit(
                    chapter_event(
                        chapter, "downloading", downloaded, skipped, failed, total
                    )
                )
                try:
                    content = scraper.fetch_chapter(chapter)
                except (HttpError, ValueError) as exc:
                    failed += 1
                    job.emit(
                        chapter_event(
                            chapter,
                            "failed",
                            downloaded,
                            skipped,
                            failed,
                            total,
                            str(exc),
                        )
                    )
                    continue

                if content.locked:
                    skipped += 1
                    job.emit(
                        chapter_event(
                            chapter,
                            "skipped",
                            downloaded,
                            skipped,
                            failed,
                            total,
                            "Terkunci, dilewati",
                        )
                    )
                    continue

                contents.append(content)
                downloaded += 1
                job.emit(
                    chapter_event(
                        chapter, "done", downloaded, skipped, failed, total
                    )
                )

            if not contents:
                if cancelled:
                    job.emit(
                        {
                            "type": "done",
                            "cancelled": True,
                            "downloaded": 0,
                            "skipped": skipped,
                            "failed": failed,
                            "file": None,
                            "filename": None,
                        }
                    )
                    job.finish("done")
                    return
                if skipped and not failed:
                    job.emit(
                        {
                            "type": "done",
                            "cancelled": False,
                            "downloaded": 0,
                            "skipped": skipped,
                            "failed": 0,
                            "file": None,
                            "filename": None,
                            "message": "Semua chapter yang dipilih terkunci.",
                        }
                    )
                    job.finish("done")
                    return
                raise ValueError("Tidak ada chapter yang berhasil diunduh.")

            job.emit(
                {"type": "stage", "stage": "export", "message": "Menyusun berkas..."}
            )
            directory = Path(tempfile.mkdtemp(prefix="novelin-web-"))
            job.directory = directory
            filename = f"{safe_filename(novel.slug or novel.title)}.{request.format}"
            output = directory / filename

            if request.format == "epub":
                cover = None
                if request.include_cover:
                    job.emit(
                        {
                            "type": "stage",
                            "stage": "cover",
                            "message": "Mengambil cover...",
                        }
                    )
                    cover = scraper.download_cover(novel)
                export_epub(novel, contents, output, cover=cover)
            elif request.format == "txt":
                export_txt(novel, contents, output)
            else:
                export_json(novel, contents, output)

            job.output = output
            job.filename = filename
            job.emit(
                {
                    "type": "done",
                    "cancelled": cancelled,
                    "downloaded": downloaded,
                    "skipped": skipped,
                    "failed": failed,
                    "file": f"/api/jobs/{job.id}/download",
                    "filename": filename,
                }
            )
            job.finish("done")

        except (HttpError, ValueError) as exc:
            job.error = str(exc)
            job.emit({"type": "error", "message": str(exc)})
            job.finish("error")
        except Exception as exc:  # noqa: BLE001 - surface unexpected failures to the UI
            job.error = f"Kesalahan tak terduga: {exc}"
            job.emit({"type": "error", "message": job.error})
            job.finish("error")
