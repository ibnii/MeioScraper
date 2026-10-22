# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

delegated: Flask untuk server lokal + HTML/CSS/vanilla ES modules tanpa build step. Dipilih
karena scraper sudah Python dan surface ini adalah alat operasional lokal, bukan situs publik.

## Users

Pembaca novel berbahasa Indonesia yang ingin membaca chapter yang dapat diakses dari
`meionovels.com` langsung di browser atau menyimpannya untuk offline. (inferred) Mereka
membuka tool ini sesekali di laptop, sudah punya URL novel, dan lebih memilih memilih
chapter secara visual daripada menulis rentang angka di terminal.

## Product Purpose

Memudahkan membaca chapter langsung di browser dan mengekspor novel ke EPUB/TXT/JSON
lewat antarmuka web lokal, dengan status gratis/terkunci yang jelas dan progres unduhan
yang terlihat.

## Positioning

Scraper lokal yang jujur soal akses: chapter gratis bisa diunduh, chapter berbayar
diperlakukan sebagai terkunci dan tidak dibobol. Fokusnya pada pemilihan chapter yang
cepat, transparan, dan hasil EPUB yang rapi.

## Operating Context

Dijalankan di laptop pengguna, satu pengguna, biasanya untuk satu novel per sesi. Input
berupa URL novel atau slug. Output disimpan ke folder unduhan pengguna.

## Capabilities and Constraints

- Muat metadata novel, daftar chapter, status `[Gratis]`/`[1 koin]`, dan cover.
- Baca chapter langsung di web dengan navigasi prev/next, ukuran huruf, dan tema
  Kertas/Sepia/Malam, plus mode immersive (klik area baca untuk menyembunyikan kontrol).
- Dark mode global lewat toggle di topbar; preferensi tersimpan dan reader mengikuti
  mode gelap saat belum ada preferensi tema reader.
- Rekomendasi novel berbentuk daftar teks di dashboard, bisa diklik untuk langsung memuat.
- Pilih chapter lewat checkbox, filter, cari, dan pilih semua yang gratis.
- Ekspor EPUB, TXT, atau JSON; progres per chapter lewat SSE.
- Cookie opsional untuk chapter yang memang dapat dibuka akun pengguna.
- Tidak ada mekanisme bypass paywall; chapter yang tetap terkunci dilewati.
- Hanya host `meionovels.com`.
- (inferred) Tidak ada akun, database, atau penyimpanan permanen; job unduhan sementara.

## Brand Commitments

Nama **Novelin**. Arah visual yang dipilih pengguna: editorial hangat — kertas krem, tinta
gelap, tipografi serif, aksen terracotta/amber. Nada bahasa Indonesia yang tenang dan jelas.

## Evidence on Hand

Kode scraper Python yang sudah bekerja, 27 unit test, dan smoke test live ke BTTH. Tidak ada
aset merek, foto, atau testimoni; jangan mengarang klaim komersial.

## Product Principles

- Akses yang sah dulu: kejelasan status mengalahkan jumlah chapter yang bisa diunduh.
- Baca dulu, unduh kalau perlu: reader harus nyaman tanpa memaksa membuat berkas.
- Pilih dulu, unduh kemudian: pengguna harus tahu persis apa yang akan diekspor.
- Progres harus terlihat dan bisa dihentikan tanpa kehilangan hasil sebelumnya.
- Hasil akhir harus rapi dibuka di pembaca EPUB mana pun.

## Accessibility & Inclusion

Target WCAG AA: kontras teks minimal 4.5:1, fokus keyboard terlihat, kontrol dapat dipakai
tanpa mouse, dan status tidak hanya dibedakan lewat warna.
