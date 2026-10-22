# AGENTS.md

## Overview

Novelin adalah scraper `meionovels.com` (WordPress + tema Madara) dengan CLI dan web app
lokal. Fungsinya: mengambil metadata novel, daftar chapter, dan konten chapter yang dapat
diakses, lalu mengekspor ke EPUB/TXT/JSON. Chapter berbayar (`[1 koin]`) **tidak** di-bypass.

## Stack

- Python >= 3.9
- `requests` (HTTP + retry/throttle)
- `beautifulsoup4` (parsing HTML)
- `flask` (web app lokal + SSE)
- `pytest` (dev)
- Frontend: HTML/CSS/vanilla ES modules, tanpa build step
- Font self-hosted: Spectral + Public Sans (lihat `novelin/web/static/fonts`)

## Key Files

| Path | Fungsi |
| --- | --- |
| `novelin/cli.py` | Argparse, subcommand `info`/`chapters`/`download`, ringkasan output |
| `novelin/scraper.py` | Normalisasi URL, fetch novel, daftar chapter via AJAX, cover |
| `novelin/parser.py` | Parser metadata, daftar chapter, konten, sanitasi HTML, teks |
| `novelin/http.py` | Session, throttle, retry, error HTTP |
| `novelin/utils.py` | Slug URL, nama file aman, parser rentang chapter |
| `novelin/models.py` | Dataclass `Novel`, `Chapter`, `ChapterContent`, `CoverImage` |
| `novelin/exporters/epub.py` | EPUB 3 manual (zipfile), cover, nav, NCX |
| `novelin/exporters/text.py` | Ekspor TXT |
| `novelin/exporters/json_export.py` | Ekspor JSON |
| `novelin/web/app.py` | Flask app factory, route `/api/novel`, `/api/chapter`, `/api/jobs`, SSE, download |
| `novelin/web/jobs.py` | JobManager, worker unduhan, cleanup |
| `novelin/web/events.py` | Iterator SSE dari antrean event job |
| `novelin/web/payloads.py` | Bentuk payload event per chapter |
| `novelin/web/templates/index.html` | Shell web: lookup, novel, ledger, export panel |
| `novelin/web/static/css/` | `tokens`, `layout`, `workspace`, `recommendations`, `controls`, `ledger`, `export`, `feedback`, `reader`, `responsive`, `theme` |
| `novelin/web/static/js/` | `app.js`, `novel.js`, `chapters.js`, `job.js`, `reader.js`, `recommendations.js`, `theme.js`, `render.js`, `api.js` |
| `tests/` | Unit test scraper, exporter, dan web API dengan fixture sintetis |
| `PRODUCT.md` / `DESIGN.md` | Konteks produk dan sistem visual web |
| `.impeccable/` | Surface brief, sidecar token, screenshot review |

## Commands

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'

.venv/bin/novelin-web [--host 127.0.0.1] [--port 5000] [--no-browser]
.venv/bin/novelin info <url|slug>
.venv/bin/novelin chapters <url|slug> [--json]
.venv/bin/novelin download <url|slug> [-f epub|txt|json] [-o PATH] [--chapters 1-20]
.venv/bin/python -m pytest
```

## Gotchas

- **Daftar chapter bukan di HTML novel.** Endpoint-nya
  `POST https://meionovels.com/novel/<slug>/ajax/chapters/?t=<page>` dan wajib mengirim
  `Referer` + `X-Requested-With: XMLHttpRequest`.
- **Urutan daftar = terbaru → terlama.** `order_chapters()` membalik daftar dan mengisi
  `Chapter.index` 1..N. Jangan mengubah ini tanpa menyesuaikan test.
- **Satu halaman bisa memuat ribuan chapter.** BTTH (1648 chapter) datang dalam satu
  respons ~700 KB. Pagination hanya diikuti jika ada `.pagination [data-page]`.
- **Deteksi paywall dua lapis:** label `.mck-label` di daftar (`[Gratis]` vs `[1 koin]`),
  lalu `.mck-gate` di halaman chapter. Jangan menghapus pengecekan gate dan jangan
  menambahkan logika bypass.
- **Cookie opsional** (`--cookie` / `MEIO_COOKIE` / field web) hanya untuk konten yang bisa
  dibuka akun pengguna. Chapter yang tetap terkunci akan dilewati. Cookie web tidak
  ditulis ke disk dan tidak boleh masuk log.
- **Reader memakai `POST /api/chapter`** dengan cookie di body, bukan query string.
  URL chapter divalidasi `normalize_chapter_url`; konten disanitasi parser yang sama.
  Request baca dibatasi throttle bersama 0,8 detik di `_default_chapter_loader`.
- **Chapter terkunci tanpa cookie tidak difetch reader**; dialog langsung menampilkan
  gate dan tombol isi cookie. Jangan menambahkan jalur bypass.
- **Cache reader** di-key oleh URL chapter + status cookie, dibuang saat input cookie
  berubah. Preferensi tema/ukuran disimpan di `localStorage` (`novelin:reader-*`).
- **Tombol Baca per baris** (`[data-read-index]`) membuka reader langsung ke chapter itu;
  klik baris selain tombol tetap men-toggle checkbox. `Mulai baca` memilih chapter gratis
  pertama.
- **Immersive reader**: klik `#reader-body` men-toggle `.is-immersive`; header/footer
  collapse lewat `max-height`, dialog membesar. Klik pada link/button/form dan seleksi
  teks diabaikan. Tombol `F` juga men-toggle. State immersive di-reset saat reader
  dibuka/ditutup.
- **Rekomendasi dashboard** adalah daftar statis di `recommendations.js` (sumber: halaman
  populer meionovels). Klik memanggil `loadNovel(slug)`. Section disembunyikan oleh
  `body.has-novel` dan saat skeleton loading.
- **Dark mode** memakai token di `html[data-theme="dark"]` (`tokens.css`) plus override
  warna hardcoded di `theme.css` yang dimuat terakhir. Preferensi `novelin:theme`
  disimpan di localStorage dan diterapkan inline di `<head>` untuk mencegah flash.
  Shell tetap lebih gelap dari page; jangan membalik hierarki light theme.
- **Reader default theme** mengikuti `novelin:reader-theme`; jika belum ada dan aplikasi
  dark, reader memakai `night`.
- **Hanya host `meionovels.com`.** URL chapter dari daftar difilter; URL chapter
  dinormalisasi ke halaman novelnya.
- **Satu job aktif di web.** `JobManager.create()` melempar `BusyError` → HTTP 409.
  Worker web melakukan fetch ulang novel + daftar chapter di server.
- **SSE** ada di `/api/jobs/<id>/events`; event terminal `done`/`error` mengakhiri stream.
  Worker menulis hasil ke `tempfile.mkdtemp()`, job lama dibersihkan setelah 2 jam.
- **Flask dev server** hanya untuk lokal; jangan bind ke `0.0.0.0` tanpa alasan.
- **CSS dipisah** per tanggung jawab dan dimuat berurutan: `tokens`, `layout`,
  `workspace`, `controls`, `ledger`, `export`, `feedback`, `responsive`. Semua override
  responsif dan keyframes berada di `responsive.css` yang dimuat terakhir, jadi jangan
  menaruh media query komponen di file komponennya tanpa alasan.
- **`[hidden]`** dipaksa `display:none !important` di `tokens.css` karena `.novel` memakai
  `display:grid` dan bisa mengalahkan atribut `hidden` bawaan.
- **bs4 di environment ini** tidak menerima `formatter="xml"`; gunakan
  `decode_contents(formatter=XMLFormatter())`.
- **Throttle bersifat per-instance `HttpClient`.** Default 1 detik; jangan menurunkan
  default tanpa alasan.
- **EPUB** ditulis manual: `mimetype` harus entry pertama dan `ZIP_STORED`; semua
  XHTML/OPF/NCX diverifikasi XML-valid oleh test.
- File inti dijaga < 300 baris; pecah per tanggung jawab jika menambah fitur besar.
