# Novelin

Scraper novel [meionovels.com](https://meionovels.com/) dengan dua antarmuka:

- **Web app lokal** untuk membaca chapter langsung, memilih chapter secara visual,
  memantau progres, dan mengunduh.
- **CLI** untuk alur cepat atau otomasi.

Keduanya mengekspor ke **EPUB**, **TXT**, atau **JSON**.

## Batasan penting

- Chapter berlabel `[1 koin]` terkunci di balik login/koin. Tool ini **tidak** membobol
  paywall; chapter seperti itu dilewati.
- Kalau kamu punya akses sah, masukkan cookie sesimu lewat opsi Cookie di web atau
  `--cookie` / `MEIO_COOKIE` di CLI. Tool hanya mengambil konten yang memang bisa dibuka
  oleh akunmu.
- Hormati ketentuan situs. Default jeda antar request adalah 1 detik; naikkan jika perlu.
  Gunakan hanya untuk konten yang kamu berhak akses.

## Instalasi

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
```

## Versi web

```bash
.venv/bin/novelin-web
# buka http://127.0.0.1:5000
```

Opsi: `--host`, `--port` (default `5000`), `--no-browser`.

Alurnya:

1. Di dashboard ada daftar **Rekomendasi** teks (mis. Pendeta Kegilaan, BTTH, Swallowed
   Star). Klik salah satu untuk langsung memuat novelnya, atau tempel URL/slug sendiri.
2. Klik **Mulai baca** atau tombol **Baca** di baris chapter. Tombol **Baca** langsung
   membuka chapter tersebut.
3. Saat membaca, **klik area baca** untuk menyembunyikan header/footer dan masuk mode
   immersive; klik lagi atau tekan `F` untuk menampilkan kontrol. `Esc` menutup reader.
4. Gunakan tombol sebelumnya/berikutnya atau panah kiri/kanan untuk pindah chapter.
5. Atur ukuran huruf dengan `A−`/`A+` dan pilih tema **Kertas / Sepia / Malam**.
   Preferensi tersimpan di browser.
6. Toggle **Gelap / Terang** di topbar untuk dark mode seluruh aplikasi. Pilihan tersimpan;
   reader otomatis memakai **Malam** saat aplikasi gelap dan belum ada preferensi reader.
7. Filter **Semua / Gratis / Terkunci**, cari judul/nomor, dan pilih chapter untuk diunduh.
8. Pilih format **EPUB / TXT / JSON**, atur cover dan opsi lanjutan.
9. Klik **Unduh N chapter**. Progres per chapter tampil lewat SSE; unduhan bisa
   dihentikan dan chapter yang sudah selesai tetap disimpan.

### Mode baca

Reader mengambil chapter lewat `POST /api/chapter` dengan cookie di body (bukan di URL),
lalu menampilkan HTML yang sudah disanitasi. Chapter gratis langsung terbaca. Chapter
`[1 koin]` menampilkan gate dan tombol **Isi cookie akun**; reader tidak mencoba membuka
paksa chapter berbayar tanpa cookie. Konten di-cache per chapter selama sesi, dan cache
dibuang saat cookie berubah.

Catatan web:

- Hanya satu unduhan aktif pada satu waktu (request kedua mendapat `409`).
- Cookie hanya disimpan di memori proses selama job berjalan dan tidak ditulis ke disk.
- File hasil berada di direktori sementara dan dibersihkan saat job lama dibersihkan.
- Server default hanya mendengarkan `127.0.0.1`.

## CLI

```bash
# Metadata novel
.venv/bin/novelin info https://meionovels.com/novel/btth/

# Daftar chapter + status gratis/terkunci
.venv/bin/novelin chapters https://meionovels.com/novel/btth/
.venv/bin/novelin chapters https://meionovels.com/novel/btth/ --json

# Unduh chapter gratis menjadi EPUB (default)
.venv/bin/novelin download https://meionovels.com/novel/btth/

# Pilih chapter dan format
.venv/bin/novelin download https://meionovels.com/novel/btth/ \
  --chapters 1-20,25 -f txt -o downloads

# JSON
.venv/bin/novelin download https://meionovels.com/novel/btth/ \
  --chapters 1647 -f json -o hasil.json
```

Slug juga bisa dipakai langsung, misalnya `novelin info btth`.

### Opsi umum

| Opsi | Default | Keterangan |
| --- | --- | --- |
| `--delay` | `1.0` | Jeda antar request dalam detik |
| `--timeout` | `30` | Timeout request dalam detik |
| `--retries` | `3` | Percobaan ulang untuk error jaringan/5xx |
| `--cookie` | env `MEIO_COOKIE` | Cookie sesi untuk chapter milik akunmu |
| `--chapters` | semua | Rentang chapter: `1-10,15,20-` |
| `-f`, `--format` | `epub` | `epub`, `txt`, atau `json` |
| `-o`, `--output` | `./downloads` | File atau direktori keluaran |

Chapter yang terkunci dilaporkan di ringkasan dan tidak dimasukkan ke file keluaran.
Kalau tidak ada satu pun chapter yang bisa diunduh, perintah keluar dengan kode 1.

## Cara kerja

- Situs memakai WordPress + tema Madara.
- Daftar chapter diambil lewat `POST /novel/<slug>/ajax/chapters/?t=<page>` dengan header
  `Referer` dan `X-Requested-With`.
- Daftar dari situs berurutan terbaru → terlama; scraper membaliknya dan memberi nomor
  urut kronologis.
- Status terkunci dibaca dari label `[Gratis]` / `[1 koin]`, lalu dikonfirmasi lagi dari
  elemen `.mck-gate` saat halaman chapter diambil.
- Web app memakai Flask + SSE. Job berjalan di thread, menulis hasil ke direktori
  sementara, lalu stream progres ke browser.
- Reader memakai `POST /api/chapter`, membaca satu halaman chapter, menyaring HTML lewat
  parser yang sama, dan menampilkan gate jika chapter terkunci. Request baca dibatasi
  jeda 0,8 detik agar tetap sopan ke sumber.

## Development

```bash
.venv/bin/python -m pytest
```

Fixture test bersifat sintetis dan tidak memakai konten novel asli. Sistem visual web
tercatat di `DESIGN.md` dan `.impeccable/design.json`.
