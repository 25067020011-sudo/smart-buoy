# Laporan Audit Repositori SMMB

- **Repo:** `/home/claude/repoaudit/smart-buoy`
- **Waktu audit:** 2026-11-11 23:49
- **Skor kesehatan:** **31/100** (100 × 100 / (100 + penalti); critical 15, high 7, medium 3, low 1)  ·  **Status:** BELUM SIAP dipakai untuk pengambilan data penelitian
- **Jumlah temuan:** 🔴 critical 6 · 🟠 high 10 · 🟡 medium 14 · 🔵 low 17 · ⚪ info 5

## Daftar temuan

| # | ID | Tingkat | Area | Temuan | Lokasi |
|---|---|---|---|---|---|
| 1 | B02 | 🔴 critical | Keamanan | RLS tidak diaktifkan pada 10 tabel | `db/schema.sql` |
| 2 | C01 | 🔴 critical | Integritas data | Sensor suhu gagal diganti nilai tetap 29.5 °C | `firmware/esp32_smmb/esp32_smmb.ino:61` |
| 3 | C02 | 🔴 critical | Integritas data | pH tidak diukur — dikirim konstanta 8.1 | `firmware/esp32_smmb/esp32_smmb.ino:86` |
| 4 | C03 | 🔴 critical | Integritas data | Posisi GPS hard-coded dan gps_fix selalu true | `firmware/esp32_smmb/esp32_smmb.ino:91` |
| 5 | C04 | 🔴 critical | Integritas data | Pengiriman 4G hanya simulasi dan selalu melapor sukses | `firmware/esp32_smmb/esp32_smmb.ino:164` |
| 6 | F04 | 🔴 critical | Integritas data | Mode demo mengekspor data sintetis tanpa penanda | `dashboard/app.py:334` |
| 7 | A01 | 🟠 high | Repo | Tidak ada berkas LICENSE |  |
| 8 | B03 | 🟠 high | Keamanan/Fungsi | Hash API key seed TIDAK cocok dengan kunci yang ditulis | `db/schema.sql:292` |
| 9 | B04 | 🟠 high | Keamanan | Kunci perangkat default dipublikasikan di repo | `firmware/esp32_smmb/config.h.example:13` |
| 10 | C05 | 🟠 high | Integritas data | Konversi EC dan salinitas bukan PSS-78 dan tanpa kompensasi suhu | `firmware/esp32_smmb/esp32_smmb.ino:81` |
| 11 | C06 | 🟠 high | Integritas data | Nomor urut (seq) disimpan di RTC RAM — reset ke 1 saat daya putus | `firmware/esp32_smmb/esp32_smmb.ino:29` |
| 12 | C07 | 🟠 high | Integritas data | Payload tidak berisi timestamp pengukuran (ts) | `firmware/esp32_smmb/esp32_smmb.ino:128` |
| 13 | E04 | 🟠 high | Edge Function | Record tanpa ts diberi waktu server | `db/supabase/functions/ingest/index.ts:70` |
| 14 | F01 | 🟠 high | Dashboard | Data live diurutkan terbaru-dulu tetapi 'latest' = iloc[-1] | `dashboard/app.py:129` |
| 15 | F02 | 🟠 high | Dashboard | Form validasi menampilkan 'berhasil disimpan' tanpa menyimpan apa pun | `dashboard/app.py:316` |
| 16 | F03 | 🟠 high | Dashboard | 4 indikator ditulis tetap (hard-coded), bukan dihitung | `dashboard/app.py:190` |
| 17 | A03 | 🟡 medium | Repo | Tidak ada test otomatis |  |
| 18 | C08 | 🟡 medium | Integritas data | ADC ESP32 dibaca mentah tanpa koreksi non-linearitas | `firmware/esp32_smmb/esp32_smmb.ino:69` |
| 19 | C09 | 🟡 medium | Integritas data | GPIO12 dipakai sebagai switch MOSFET (pin strapping) | `firmware/esp32_smmb/config.h.example:37` |
| 20 | D02 | 🟡 medium | Basis data | Uji QARTOD 'spike' didefinisikan di enum tetapi tidak diimplementasikan | `db/schema.sql:10` |
| 21 | D03 | 🟡 medium | Basis data | Alarm 'no_data' ada di enum tetapi tidak ada job pembuatnya | `db/schema.sql:12` |
| 22 | E01 | 🟡 medium | Edge Function | Tidak ada batas ukuran batch | `db/supabase/functions/ingest/index.ts:38` |
| 23 | E06 | 🟡 medium | Edge Function | Insert measurements & telemetry tidak atomik | `db/supabase/functions/ingest/index.ts:87` |
| 24 | E07 | 🟡 medium | Edge Function | Tidak ada validasi tipe/rentang nilai payload | `db/supabase/functions/ingest/index.ts:69` |
| 25 | F05 | 🟡 medium | Dashboard | Pilihan perangkat di sidebar tidak memfilter data | `dashboard/app.py:127` |
| 26 | F06 | 🟡 medium | Dashboard | Filter tanggal unduhan tidak diterapkan | `dashboard/app.py:328` |
| 27 | F07 | 🟡 medium | Dashboard | Grafik tidak menandai flag QC padahal diklaim QARTOD | `dashboard/app.py:195` |
| 28 | F08 | 🟡 medium | Keamanan | Dashboard publik membaca tabel mentah, bukan view publik | `dashboard/app.py:99` |
| 29 | G03 | 🟡 medium | Analisis | Completeness default = 100% bila expected_count tidak diisi | `analysis/dqa_assessment.py:24` |
| 30 | G05 | 🟡 medium | Analisis | Validasi hanya Bias/RMSE/R² — belum Bland–Altman & Deming | `analysis/dqa_assessment.py:82` |
| 31 | A02 | 🔵 low | Repo | Tidak ada CITATION.cff |  |
| 32 | A04 | 🔵 low | Repo | Tidak ada CI (GitHub Actions) |  |
| 33 | A05 | 🔵 low | Repo | Berkas duplikat identik | `PRD Smart Marine Monitoring Buoy (SMMB) v1.1 (2) 2.md` |
| 34 | A05 | 🔵 low | Repo | Berkas duplikat identik | `04_UI_MOCKUP 2.html` |
| 35 | A06 | 🔵 low | Repo | Arsip biner di-commit | `SMMB-docs (1).zip` |
| 36 | A06 | 🔵 low | Repo | Arsip biner di-commit | `SMMB-docs.zip` |
| 37 | A07 | 🔵 low | Repo | 4 nama berkas berisi spasi/kurung |  |
| 38 | A09 | 🔵 low | Reproduktibilitas | Versi dependensi tidak dikunci | `dashboard/requirements.txt:1` |
| 39 | C10 | 🔵 low | Integritas data | Waktu stabilisasi sensor hanya 1 detik, satu sampel per parameter | `firmware/esp32_smmb/esp32_smmb.ino:54` |
| 40 | D04 | 🔵 low | Basis data | Kolom calib_ids tidak pernah diisi oleh ingest | `db/schema.sql:87` |
| 41 | D05 | 🔵 low | Basis data | Pencocokan referensi ↔ data sensor belum otomatis | `db/schema.sql:132` |
| 42 | E03 | 🔵 low | Edge Function | Perbandingan hash kunci tidak constant-time | `db/supabase/functions/ingest/index.ts:56` |
| 43 | E05 | 🔵 low | Edge Function | device_id hanya diambil dari record pertama | `db/supabase/functions/ingest/index.ts:47` |
| 44 | E08 | 🔵 low | Edge Function | Pesan Telegram Markdown tidak di-escape | `db/supabase/functions/notify-telegram/index.ts:55` |
| 45 | E09 | 🔵 low | Edge Function | Kegagalan kirim Telegram tetap dibalas 200 | `db/supabase/functions/notify-telegram/index.ts:61` |
| 46 | F09 | 🔵 low | Dashboard | Hanya 500 baris terakhir dimuat (~5 hari) | `dashboard/app.py:99` |
| 47 | G04 | 🔵 low | Analisis | Duplikat dihitung tetapi tidak dibuang sebelum metrik lain | `analysis/dqa_assessment.py:28` |
| 48 | A08 | ⚪ info | Repo | Folder analysis/ tidak dijelaskan di README | `README.md` |
| 49 | A08 | ⚪ info | Repo | Folder tools/ tidak dijelaskan di README | `README.md` |
| 50 | A08 | ⚪ info | Repo | Folder docs/ tidak dijelaskan di README | `README.md` |
| 51 | E02 | ⚪ info | Edge Function | CORS '*' pada endpoint perangkat | `db/supabase/functions/ingest/index.ts:9` |
| 52 | G02 | ⚪ info | Kode | pyflakes: 'math' imported but unused | `dashboard/app.py:2` |

## Rincian dan perbaikan

### 🔴 B02 — RLS tidak diaktifkan pada 10 tabel
- **Lokasi:** `db/schema.sql`
- **Bukti:** `profiles, devices, sensors, calibrations, measurements, device_telemetry, field_visits, reference_measurements, qc_thresholds, alerts`
- **Dampak:** Di Supabase, tabel tanpa RLS dapat DIBACA, DIUBAH, dan DIHAPUS oleh siapa pun yang memegang anon key — dan anon key dipakai dashboard publik. Dataset penelitian bisa dimanipulasi tanpa jejak.
- **Perbaikan:** ALTER TABLE … ENABLE ROW LEVEL SECURITY untuk semua tabel; policy SELECT anon hanya lewat view publik; INSERT measurements hanya via Edge Function (service role).

### 🔴 C01 — Sensor suhu gagal diganti nilai tetap 29.5 °C
- **Lokasi:** `firmware/esp32_smmb/esp32_smmb.ino:61`
- **Bukti:** `data.temp_c = 29.5; // fallback`
- **Dampak:** Data palsu masuk dataset sebagai pengukuran sah; salinitas & DO jenuh ikut salah. Ini fabrikasi data bila lolos ke publikasi.
- **Perbaikan:** Kirim null/NaN dan biarkan QC memberi flag 9 (missing).

### 🔴 C02 — pH tidak diukur — dikirim konstanta 8.1
- **Lokasi:** `firmware/esp32_smmb/esp32_smmb.ino:86`
- **Bukti:** `data.ph = 8.1; // Contoh default air laut`
- **Dampak:** Seluruh deret pH di database adalah angka tetap, bukan pengukuran.
- **Perbaikan:** Baca PIN_PH_ANALOG + kalibrasi 2 titik, atau kirim null bila sensor belum terpasang.

### 🔴 C03 — Posisi GPS hard-coded dan gps_fix selalu true
- **Lokasi:** `firmware/esp32_smmb/esp32_smmb.ino:91`
- **Bukti:** `data.gps_fix = true;`
- **Dampak:** Geofence tidak akan pernah terpicu walau buoy hanyut/dicuri; posisi di dataset fiktif.
- **Perbaikan:** Baca NMEA dari modem (AT+CGPSINFO) dan set gps_fix=false bila belum lock.

### 🔴 C04 — Pengiriman 4G hanya simulasi dan selalu melapor sukses
- **Lokasi:** `firmware/esp32_smmb/esp32_smmb.ino:164`
- **Bukti:** `delay(1500); // Simulasi transaksi HTTP`
- **Dampak:** Tidak ada data yang benar-benar terkirim; kolom 'sent' di microSD tidak pernah diperbarui; store-and-forward (backlog) tidak ada.
- **Perbaikan:** Implementasikan AT+HTTP* (SIM7600/A7670) atau TinyGSM + SSLClient; cek kode 200 dan kirim ulang baris microSD dengan sent=0.

### 🔴 F04 — Mode demo mengekspor data sintetis tanpa penanda
- **Lokasi:** `dashboard/app.py:334`
- **Bukti:** `st.download_button(`
- **Dampak:** CSV data acak dapat terunduh dan terpakai seolah data lapangan → risiko fabrikasi data tak disengaja dalam skripsi/jurnal.
- **Perbaikan:** Nonaktifkan unduhan di mode demo, atau tambah kolom is_synthetic=True dan nama berkas *_SIMULASI.csv.

### 🟠 A01 — Tidak ada berkas LICENSE
- **Dampak:** Secara hukum orang lain tidak boleh memakai/menyalin kode & data; jurnal Q1 dan reviewer menuntut lisensi terbuka untuk 'code/data availability'.
- **Perbaikan:** Tambahkan LICENSE (mis. MIT/Apache-2.0 untuk kode, CC-BY-4.0 untuk dataset & dokumen).

### 🟠 B03 — Hash API key seed TIDAK cocok dengan kunci yang ditulis
- **Lokasi:** `db/schema.sql:292`
- **Bukti:** `komentar: 'secret123', hash sebenarnya = sha256('password')`
- **Dampak:** Firmware & simulator yang memakai 'secret123' akan selalu ditolak 403 oleh ingest.
- **Perbaikan:** Ganti dengan 'fcf730b6d95236ecd3c9fc2d92d7b6b2bb061514961aec041d6c7a7192f592e4' — lebih baik: buat kunci acak 32 byte per perangkat, jangan simpan di repo.

### 🟠 B04 — Kunci perangkat default dipublikasikan di repo
- **Lokasi:** `firmware/esp32_smmb/config.h.example:13`
- **Bukti:** `#define DEVICE_API_KEY      "secret123"`
- **Dampak:** Siapa pun dapat mengirim data palsu ke endpoint ingest bila seed dipakai saat deploy.
- **Perbaikan:** Hapus baris INSERT devices dari schema.sql produksi; buat kunci lewat skrip terpisah.

### 🟠 C05 — Konversi EC dan salinitas bukan PSS-78 dan tanpa kompensasi suhu
- **Lokasi:** `firmware/esp32_smmb/esp32_smmb.ino:81`
- **Bukti:** `data.ec_mscm = vEC * 15.0; // dummy linear scale`
- **Dampak:** Galat salinitas puluhan persen; tidak sesuai metode proposal (PSS-78/TEOS-10).
- **Perbaikan:** Kirim EC mentah + suhu; hitung salinitas di server dengan gsw.SP_from_C (TEOS-10).

### 🟠 C06 — Nomor urut (seq) disimpan di RTC RAM — reset ke 1 saat daya putus
- **Lokasi:** `firmware/esp32_smmb/esp32_smmb.ino:29`
- **Bukti:** `RTC_DATA_ATTR uint64_t bootSequence = 1;`
- **Dampak:** Setelah brown-out/ganti baterai, seq berulang → UNIQUE(device_id, seq) menolak data baru sebagai 'duplicate' → data hilang diam-diam.
- **Perbaikan:** Simpan seq di NVS (Preferences) atau gunakan epoch detik sebagai seq.

### 🟠 C07 — Payload tidak berisi timestamp pengukuran (ts)
- **Lokasi:** `firmware/esp32_smmb/esp32_smmb.ino:128`
- **Bukti:** `String buildJsonPayload(const SensorData &d, uint64_t seq) {`
- **Dampak:** Ingest memakai waktu server; data backlog akan bertimestamp salah — merusak analisis pasang surut & aliasing.
- **Perbaikan:** Sertakan ts UTC dari RTC/GPS di setiap record; ingest menolak record tanpa ts.

### 🟠 E04 — Record tanpa ts diberi waktu server
- **Lokasi:** `db/supabase/functions/ingest/index.ts:70`
- **Bukti:** `const tsUtc = item.ts || new Date().toISOString();`
- **Dampak:** Data backlog dari microSD akan tercatat pada jam kirim, bukan jam ukur.
- **Perbaikan:** Tolak (rejected) record tanpa ts; validasi ts tidak di masa depan > 5 menit.

### 🟠 F01 — Data live diurutkan terbaru-dulu tetapi 'latest' = iloc[-1]
- **Lokasi:** `dashboard/app.py:129`
- **Bukti:** `latest = df_data.iloc[-1]`
- **Dampak:** Saat terhubung Supabase, kartu 'terkini' dan grafik '24 jam terakhir' menampilkan data TERLAMA dari 500 baris (mode demo tidak terkena karena data demo urut naik).
- **Perbaikan:** df = df.sort_values('ts_utc') setelah load_data().

### 🟠 F02 — Form validasi menampilkan 'berhasil disimpan' tanpa menyimpan apa pun
- **Lokasi:** `dashboard/app.py:316`
- **Bukti:** `st.success("✅ Data kunjungan berhasil disimpan ke database!")`
- **Dampak:** Data referensi lapangan (inti RQ1–RQ3) hilang padahal teknisi mengira tersimpan.
- **Perbaikan:** Insert ke field_visits + reference_measurements (butuh login & RLS), tampilkan error nyata.

### 🟠 F03 — 4 indikator ditulis tetap (hard-coded), bukan dihitung
- **Lokasi:** `dashboard/app.py:190`
- **Bukti:** `kpi_col1.progress(98, text="Data Availability Bulan Ini: 98.4%")`
- **Dampak:** Availability 98,4%, 'Alarm Aktif 0', dan status 'Aman' tampil walau kenyataannya berbeda — menyesatkan pengguna dan reviewer.
- **Perbaikan:** Hitung dari v_daily_availability, tabel alerts (status <> 'resolved'), dan dist_from_anchor_m.

### 🟡 A03 — Tidak ada test otomatis
- **Dampak:** Fungsi QC, DQA, dan konversi sensor tidak teruji; kesalahan rumus tidak terdeteksi.
- **Perbaikan:** Tambahkan tests/ dengan pytest (DQA, simulator, konversi salinitas) dan uji SQL trigger.

### 🟡 C08 — ADC ESP32 dibaca mentah tanpa koreksi non-linearitas
- **Lokasi:** `firmware/esp32_smmb/esp32_smmb.ino:69`
- **Bukti:** `int rawBatt = analogRead(PIN_BATT_ADC);`
- **Dampak:** ADC ESP32 tidak linear (terutama < 0,15 V dan > 2,5 V) → bias turbiditas & EC.
- **Perbaikan:** Gunakan analogReadMilliVolts() + rata-rata/median N sampel; idealnya ADC eksternal ADS1115.

### 🟡 C09 — GPIO12 dipakai sebagai switch MOSFET (pin strapping)
- **Lokasi:** `firmware/esp32_smmb/config.h.example:37`
- **Bukti:** `#define PIN_PWR_SENSORS     12  // MOSFET Switch Daya Sensor (Active HIGH)`
- **Dampak:** Bila GPIO12 tertarik HIGH saat boot, ESP32 memilih tegangan flash 1,8 V dan gagal boot.
- **Perbaikan:** Pindahkan ke GPIO25/26/27 atau pastikan pull-down saat boot.

### 🟡 D02 — Uji QARTOD 'spike' didefinisikan di enum tetapi tidak diimplementasikan
- **Lokasi:** `db/schema.sql:10`
- **Bukti:** `create type qc_test       as enum ('gross_range', 'spike', 'flat_line', 'rate_of_change');`
- **Dampak:** Hanya gross range yang berjalan; lonjakan & sensor macet tidak terdeteksi.
- **Perbaikan:** Implementasikan di pipeline Python (ioos_qc) terjadwal, atau trigger yang membaca N data terakhir.

### 🟡 D03 — Alarm 'no_data' ada di enum tetapi tidak ada job pembuatnya
- **Lokasi:** `db/schema.sql:12`
- **Bukti:** `create type alert_type    as enum ('geofence', 'battery_low', 'no_data', 'out_of_range', 'leak');`
- **Dampak:** Bila buoy mati/dicuri, tidak ada alarm 'data terhenti' — padahal ini KPI utama.
- **Perbaikan:** pg_cron tiap 15 menit: INSERT alert no_data bila max(received_at) < now() - 60 menit.

### 🟡 E01 — Tidak ada batas ukuran batch
- **Lokasi:** `db/supabase/functions/ingest/index.ts:38`
- **Bukti:** `const records = Array.isArray(body) ? body : [body];`
- **Dampak:** Satu request bisa berisi ribuan record (DoS / kuota Supabase habis).
- **Perbaikan:** Tolak batch > 200 record dan body > 256 KB.

### 🟡 E06 — Insert measurements & telemetry tidak atomik
- **Lokasi:** `db/supabase/functions/ingest/index.ts:87`
- **Bukti:** `const { error: tErr } = await supabase.from("device_telemetry").insert({`
- **Dampak:** Bila telemetry gagal, record dilaporkan 'rejected' → perangkat kirim ulang → measurement dianggap duplikat dan telemetry hilang permanen.
- **Perbaikan:** Satukan dalam fungsi SQL (supabase.rpc('ingest_record', …)) dalam satu transaksi.

### 🟡 E07 — Tidak ada validasi tipe/rentang nilai payload
- **Lokasi:** `db/supabase/functions/ingest/index.ts:69`
- **Bukti:** `const seq = item.seq;`
- **Perbaikan:** Validasi skema (zod) — seq integer ≥ 0, ts ISO-8601, angka finite.

### 🟡 F05 — Pilihan perangkat di sidebar tidak memfilter data
- **Lokasi:** `dashboard/app.py:127`
- **Bukti:** `selected_device = st.sidebar.selectbox("Pilih Perangkat", device_list, index=0)`

### 🟡 F06 — Filter tanggal unduhan tidak diterapkan
- **Lokasi:** `dashboard/app.py:328`
- **Bukti:** `start_date = col_d1.date_input("Mulai Tanggal", datetime.date.today() - datetime.timedelta(days=7))`
- **Perbaikan:** Filter df berdasarkan rentang tanggal sebelum to_csv().

### 🟡 F07 — Grafik tidak menandai flag QC padahal diklaim QARTOD
- **Lokasi:** `dashboard/app.py:195`
- **Bukti:** `# TAB 2: TRENDS DENGAN QC FLAGS (QARTOD)`
- **Perbaikan:** Warnai titik per flag (1 hijau, 3 kuning, 4 merah) dan opsi sembunyikan flag 4.

### 🟡 F08 — Dashboard publik membaca tabel mentah, bukan view publik
- **Lokasi:** `dashboard/app.py:99`
- **Bukti:** `res_m = supabase_client.table("measurements").select("*").order("ts_utc", desc=True).limit(500).execute()`
- **Dampak:** Butuh akses anon ke tabel mentah (koordinat presisi, data gagal QC).
- **Perbaikan:** Baca v_public_measurements untuk publik; tabel mentah hanya untuk peneliti yang login.

### 🟡 G03 — Completeness default = 100% bila expected_count tidak diisi
- **Lokasi:** `analysis/dqa_assessment.py:24`
- **Bukti:** `expected_count = total_records`
- **Dampak:** Grade A bisa keluar walau data bolong berhari-hari.
- **Perbaikan:** Hitung expected dari rentang waktu deployment / interval (seperti dqa.py di SMMB-docs).

### 🟡 G05 — Validasi hanya Bias/RMSE/R² — belum Bland–Altman & Deming
- **Lokasi:** `analysis/dqa_assessment.py:82`
- **Bukti:** `correlation_matrix = np.corrcoef(s, r)`
- **Dampak:** Proposal (Bab III) menjanjikan Bland–Altman LoA dan regresi Deming; R² tidak mengukur kesesuaian.
- **Perbaikan:** Tambah LoA (bias ± 1,96 SD) dan Deming; dqa.py versi SMMB-docs sudah memuat fungsi dasarnya.

### 🔵 A02 — Tidak ada CITATION.cff
- **Perbaikan:** Tambahkan CITATION.cff dan arsipkan rilis di Zenodo agar mendapat DOI.

### 🔵 A04 — Tidak ada CI (GitHub Actions)
- **Perbaikan:** Workflow: pyflakes/ruff + pytest + jalankan schema.sql di service PostgreSQL.

### 🔵 A05 — Berkas duplikat identik
- **Lokasi:** `PRD Smart Marine Monitoring Buoy (SMMB) v1.1 (2) 2.md`
- **Bukti:** `sama dengan PRD Smart Marine Monitoring Buoy (SMMB) v1.1 (2).md`
- **Perbaikan:** Hapus salinan (nama berakhiran ' 2', '(1)', '(2)').

### 🔵 A05 — Berkas duplikat identik
- **Lokasi:** `04_UI_MOCKUP 2.html`
- **Bukti:** `sama dengan 04_UI_MOCKUP.html`
- **Perbaikan:** Hapus salinan (nama berakhiran ' 2', '(1)', '(2)').

### 🔵 A06 — Arsip biner di-commit
- **Lokasi:** `SMMB-docs (1).zip`
- **Perbaikan:** Jangan commit .zip; simpan dokumen sebagai berkas teks (docs/) atau lampirkan di Release.

### 🔵 A06 — Arsip biner di-commit
- **Lokasi:** `SMMB-docs.zip`
- **Perbaikan:** Jangan commit .zip; simpan dokumen sebagai berkas teks (docs/) atau lampirkan di Release.

### 🔵 A07 — 4 nama berkas berisi spasi/kurung
- **Bukti:** `04_UI_MOCKUP 2.html, PRD Smart Marine Monitoring Buoy (SMMB) v1.1 (2) 2.md, PRD Smart Marine Monitoring Buoy (SMMB) v1.1 (2).md, SMMB-docs (1).zip`
- **Perbaikan:** Ganti dengan nama-pendek-tanpa-spasi, mis. docs/PRD_v1.1.md.

### 🔵 A09 — Versi dependensi tidak dikunci
- **Lokasi:** `dashboard/requirements.txt:1`
- **Bukti:** `streamlit>=1.30.0`
- **Perbaikan:** Kunci versi (==) atau sertakan requirements.lock agar hasil dapat direproduksi.

### 🔵 C10 — Waktu stabilisasi sensor hanya 1 detik, satu sampel per parameter
- **Lokasi:** `firmware/esp32_smmb/esp32_smmb.ino:54`
- **Bukti:** `delay(1000); // Waktu stabilisasi sensor & op-amp`
- **Dampak:** Sensor EC/turbiditas/pH butuh 5–30 s; satu sampel rentan derau.
- **Perbaikan:** Pemanasan sesuai datasheet + median dari ≥ 10 sampel (sesuai proposal Bag. 3.5.5).

### 🔵 D04 — Kolom calib_ids tidak pernah diisi oleh ingest
- **Lokasi:** `db/schema.sql:87`
- **Bukti:** `calib_ids   jsonb,`
- **Dampak:** Ketertelusuran kalibrasi per data (syarat GUM/metrologi di proposal) hilang.
- **Perbaikan:** Ingest mengisi calib_ids dari kalibrasi aktif (valid_to is null) per sensor.

### 🔵 D05 — Pencocokan referensi ↔ data sensor belum otomatis
- **Lokasi:** `db/schema.sql:132`
- **Bukti:** `matched_measurement_id bigint references measurements(id),`
- **Perbaikan:** Fungsi/trigger yang mencari record terdekat ±7,5 menit dari measured_at.

### 🔵 E03 — Perbandingan hash kunci tidak constant-time
- **Lokasi:** `db/supabase/functions/ingest/index.ts:56`
- **Bukti:** `if (devErr || !device || device.api_key_hash !== deviceKeyHash) {`

### 🔵 E05 — device_id hanya diambil dari record pertama
- **Lokasi:** `db/supabase/functions/ingest/index.ts:47`
- **Bukti:** `const deviceId = records[0].device_id;`
- **Perbaikan:** Tolak batch yang berisi device_id berbeda-beda.

### 🔵 E08 — Pesan Telegram Markdown tidak di-escape
- **Lokasi:** `db/supabase/functions/notify-telegram/index.ts:55`
- **Bukti:** `parse_mode: "Markdown",`
- **Dampak:** Karakter _ * [ ` dalam pesan membuat Telegram menolak kiriman → alarm gagal terkirim.
- **Perbaikan:** Pakai parse_mode HTML dengan escape, atau MarkdownV2 + escape.

### 🔵 E09 — Kegagalan kirim Telegram tetap dibalas 200
- **Lokasi:** `db/supabase/functions/notify-telegram/index.ts:61`
- **Bukti:** `status: 200,`
- **Perbaikan:** Kembalikan status non-200 bila res.ok false agar webhook mencoba ulang.

### 🔵 F09 — Hanya 500 baris terakhir dimuat (~5 hari)
- **Lokasi:** `dashboard/app.py:99`
- **Bukti:** `res_m = supabase_client.table("measurements").select("*").order("ts_utc", desc=True).limit(500).execute()`
- **Dampak:** Unduhan 'dataset lengkap' sebenarnya terpotong.
- **Perbaikan:** Paginasi (range) atau unduh dari Supabase Storage/ekspor terjadwal.

### 🔵 G04 — Duplikat dihitung tetapi tidak dibuang sebelum metrik lain
- **Lokasi:** `analysis/dqa_assessment.py:28`
- **Bukti:** `duplicates = df_measurements.duplicated(subset=["device_id", "seq"]).sum()`

### ⚪ E02 — CORS '*' pada endpoint perangkat
- **Lokasi:** `db/supabase/functions/ingest/index.ts:9`
- **Bukti:** `"Access-Control-Allow-Origin": "*",`
- **Perbaikan:** Endpoint perangkat tidak butuh CORS; hapus agar tidak dipanggil dari browser.

## Yang sudah baik

- ✅ Tidak ditemukan pola secret (JWT, token Telegram, API key) di berkas teks
- ✅ .gitignore mengecualikan secrets.toml dan config.h
- ✅ Firmware menulis salinan lokal ke microSD
- ✅ Firmware memakai deep sleep untuk hemat daya
- ✅ Skema memiliki trigger QC gross range
- ✅ Skema memiliki trigger geofence/baterai/bocor
- ✅ Skema memiliki view pasangan validasi
- ✅ Skema memiliki deduplikasi (device_id, seq)
- ✅ 3 berkas Python lolos py_compile
- ✅ schema.sql berhasil dijalankan di PostgreSQL lokal
- ✅ Trigger telemetri membuat alarm: geofence,battery_low,leak
- ✅ Alarm tidak dobel saat kondisi berulang
- ✅ QC gross range menandai pH 5,2 sebagai flag 4
- ✅ View publik menyaring data ber-flag 4