from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import List, Optional, Sequence

from .exporters import export_epub, export_json, export_txt
from .http import HttpClient, HttpError
from .models import Chapter, ChapterContent, Novel
from .scraper import MeionovelsScraper
from .utils import parse_chapter_range, safe_filename

FORMATS = ("epub", "txt", "json")


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--delay", type=float, default=1.0, help="Jeda antar request (detik)")
    common.add_argument("--timeout", type=float, default=30.0, help="Timeout request (detik)")
    common.add_argument("--retries", type=int, default=3, help="Jumlah percobaan ulang")
    common.add_argument(
        "--cookie",
        default=os.environ.get("MEIO_COOKIE"),
        help="Cookie login untuk chapter yang sudah kamu miliki (atau env MEIO_COOKIE)",
    )

    parser = argparse.ArgumentParser(
        prog="novelin",
        description="Scraper chapter gratis meionovels.com",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    info = subparsers.add_parser("info", parents=[common], help="Tampilkan metadata novel")
    info.add_argument("url", help="URL novel atau slug")

    chapters = subparsers.add_parser(
        "chapters", parents=[common], help="Tampilkan daftar chapter"
    )
    chapters.add_argument("url", help="URL novel atau slug")
    chapters.add_argument("--json", action="store_true", help="Cetak sebagai JSON")

    download = subparsers.add_parser(
        "download", parents=[common], help="Unduh chapter yang dapat diakses"
    )
    download.add_argument("url", help="URL novel atau slug")
    download.add_argument(
        "-f",
        "--format",
        choices=FORMATS,
        default="epub",
        help="Format keluaran (default: epub)",
    )
    download.add_argument(
        "-o",
        "--output",
        help="File atau direktori keluaran (default: ./downloads)",
    )
    download.add_argument(
        "--chapters",
        help="Pilih chapter, contoh: 1-10,15,20-",
    )
    download.add_argument("--no-cover", action="store_true", help="Jangan sertakan cover di EPUB")
    download.add_argument("-q", "--quiet", action="store_true", help="Sembunyikan progres")

    return parser


def _client(args: argparse.Namespace) -> HttpClient:
    return HttpClient(
        delay=args.delay,
        timeout=args.timeout,
        retries=args.retries,
        cookie=args.cookie,
    )


def _scraper(args: argparse.Namespace) -> MeionovelsScraper:
    return MeionovelsScraper(client=_client(args))


def _print_info(novel: Novel, chapter_total: Optional[int] = None) -> None:
    rows = [
        ("Judul", novel.title),
        ("Alternatif", novel.alternative_title),
        ("Penulis", novel.author),
        ("Artist", novel.artist),
        ("Status", novel.status),
        ("Rilis", novel.release),
        ("Genre", ", ".join(novel.genres)),
        ("Chapter", str(chapter_total) if chapter_total is not None else None),
        ("URL", novel.url),
    ]
    width = max(len(label) for label, _ in rows)
    for label, value in rows:
        if value:
            print(f"{label.ljust(width)} : {value}")
    if novel.synopsis:
        print()
        print(novel.synopsis)


def _chapter_label(chapter: Chapter) -> str:
    if chapter.locked:
        label = (chapter.price_label or "TERKUNCI").strip("[] ")
        return label or "TERKUNCI"
    return "GRATIS"


def _cmd_info(args: argparse.Namespace) -> int:
    novel = _scraper(args).fetch_novel(args.url)
    _print_info(novel)
    return 0


def _cmd_chapters(args: argparse.Namespace) -> int:
    scraper = _scraper(args)
    novel = scraper.fetch_novel(args.url)
    chapters = scraper.fetch_chapters(novel)

    if args.json:
        payload = [
            {
                "index": chapter.index,
                "title": chapter.title,
                "url": chapter.url,
                "locked": chapter.locked,
                "price_label": chapter.price_label,
                "release_date": chapter.release_date,
            }
            for chapter in chapters
        ]
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print(f"{novel.title} - {len(chapters)} chapter")
    width = len(str(len(chapters)))
    for chapter in chapters:
        print(
            f"{str(chapter.index).rjust(width)}  "
            f"[{_chapter_label(chapter)}]  {chapter.title}"
        )
    return 0


def _cmd_download(args: argparse.Namespace) -> int:
    scraper = _scraper(args)
    novel = scraper.fetch_novel(args.url)
    chapters = scraper.fetch_chapters(novel)

    selected: List[Chapter] = chapters
    if args.chapters:
        wanted = parse_chapter_range(args.chapters, total=len(chapters))
        selected = [chapter for chapter in chapters if chapter.index in wanted]

    if not selected:
        print("error: tidak ada chapter yang cocok dengan pilihan.", file=sys.stderr)
        return 1

    contents: List[ChapterContent] = []
    skipped: List[Chapter] = []
    failed: List[str] = []

    for position, chapter in enumerate(selected, start=1):
        if chapter.locked and not scraper.client.has_cookie:
            skipped.append(chapter)
            continue

        if not args.quiet:
            print(
                f"[{position}/{len(selected)}] {chapter.index}. {chapter.title}",
                file=sys.stderr,
            )

        try:
            content = scraper.fetch_chapter(chapter)
        except HttpError as exc:
            failed.append(f"{chapter.title}: {exc}")
            continue

        if content.locked:
            skipped.append(chapter)
            continue
        contents.append(content)

    if not contents:
        print(
            "error: tidak ada chapter yang bisa diunduh. "
            "Chapter berlabel koin hanya bisa diakses lewat akunmu (--cookie).",
            file=sys.stderr,
        )
        return 1

    output = _resolve_output(args.output, novel, args.format)
    if args.format == "epub":
        cover = None if args.no_cover else scraper.download_cover(novel)
        export_epub(novel, contents, output, cover=cover)
    elif args.format == "txt":
        export_txt(novel, contents, output)
    else:
        export_json(novel, contents, output)

    print(f"Tersimpan : {output}")
    print(f"Diunduh   : {len(contents)} chapter")
    if skipped:
        print(f"Dilewati  : {len(skipped)} chapter terkunci")
    if failed:
        print(f"Gagal     : {len(failed)} chapter", file=sys.stderr)
        for message in failed:
            print(f"  - {message}", file=sys.stderr)

    return 0


def _resolve_output(output: Optional[str], novel: Novel, output_format: str) -> Path:
    base = Path(output).expanduser() if output else Path("downloads")
    if base.suffix.lower() in {f".{fmt}" for fmt in FORMATS}:
        return base
    return base / f"{safe_filename(novel.slug or novel.title)}.{output_format}"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "info":
            return _cmd_info(args)
        if args.command == "chapters":
            return _cmd_chapters(args)
        if args.command == "download":
            return _cmd_download(args)
    except (HttpError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nDibatalkan.", file=sys.stderr)
        return 130

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
