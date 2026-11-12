# Smart Marine Monitoring Buoy (SMMB)

**Prototipe Buoy Pemantau Kualitas Air Laut Berbasis IoT & Data Science**  
*Institut Teknologi Sepuluh Nopember (ITS), Surabaya · 2026–2027*

---

## 📁 Struktur Repositori

```text
smart-buoy/
├── dashboard/               # Web Dashboard Streamlit (Python)
│   ├── app.py               # Aplikasi utama (Overview, Tren QC QARTOD, Peta Folium, Validasi, Export)
│   ├── requirements.txt     # Dependensi Python teruji
│   └── .streamlit/secrets.toml.example
├── db/                      # Skema Database & Serverless
│   ├── schema.sql           # Skema lengkap PostgreSQL (RLS, Enum, Tabel, Trigger, Matching, QC)
│   └── supabase/functions/
│       ├── ingest/index.ts         # Edge Function verifikasi API key & batch payload ESP32
│       └── notify-telegram/index.ts # Edge Function pengirim alarm instan ke Telegram (HTML)
├── firmware/                # Kode ESP32 (Arduino Framework)
│   └── esp32_smmb/
│       ├── esp32_smmb.ino   # Firmware siklus deep sleep, NVS Preferences, multisampling, microSD, 4G
│       └── config.h.example # Konfigurasi Pin, APN, dan Endpoint Supabase
├── analysis/                # Analisis Data & Quality Control
│   └── dqa_assessment.py    # Engine audit kualitas dataset (Completeness, Bland-Altman, Deming)
├── tools/                   # Utilitas & Pengujian
│   └── simulate_telemetry.py# Simulator transmisi IoT buoy untuk uji lab/dashboard
├── tests/                   # Pengujian Otomatis (Pytest)
│   └── test_smmb.py         # Unit test metrik DQA dan validasi simulator
├── docs/                    # Dokumentasi Teknis & SOP
│   ├── PRD_v1.0.md          # Dokumen PRD Awal (Draft 1.0)
│   ├── WIRING_DIAGRAM.md    # Skema perkabelan pinout, MOSFET load switch, dan voltage divider
│   └── SOP_CALIBRATION.md   # Prosedur kalibrasi 3-titik dan validasi berkala
├── CITATION.cff             # Metadata sitasi karya ilmiah
├── LICENSE                  # Lisensi Open Source (MIT)
└── README.md
```

---

## 🌊 Parameter Kualitas Air yang Dipantau

Sistem memantau 5 parameter inti kualitas air pesisir:
1. **Suhu Air (°C)** — Pengukuran kontinu probe submersible DS18B20.
2. **Salinitas (PSU)** — Konversi konduktivitas EC dengan kompensasi suhu (PSS-78).
3. **Kekeruhan / Turbidity (NTU)** — Pengukuran optik dalam housing gelap terkalibrasi Formazin.
4. **pH** — Probe submersible elektroda kaca dengan kalibrasi 2-titik (buffer 4.01 / 7.00).
5. **Dissolved Oxygen (DO - mg/L)** — Dipantau melalui *virtual sensor* estimasi kelarutan gas jenuh ($O_2$ saturation model) serta divalidasi berkala menggunakan instrumen referensi MPV/lab saat kunjungan lapangan.

---

## 🚀 Panduan Setup Singkat

### 1. Inisialisasi Database di Supabase
1. Buka [supabase.com](https://supabase.com) dan buat proyek baru (*Free Tier*).
2. Masuk ke **SQL Editor** di sidebar kiri.
3. Buka file `db/schema.sql`, salin seluruh isinya, lalu jalankan (**Run**). Semua tabel otomatis terlindungi oleh **Row Level Security (RLS)**.
4. Catat **Project URL** dan **Anon/Service Role Key** di menu `Project Settings > API`.

### 2. Menjalankan Dashboard Streamlit
```bash
cd dashboard
pip install -r requirements.txt
streamlit run app.py
```

### 3. Menjalankan Uji Otomatis
```bash
pytest tests/
```

---

## 📄 Lisensi & Sitasi
Didistribusikan di bawah lisensi MIT. Silakan lihat berkas [LICENSE](LICENSE) dan [CITATION.cff](CITATION.cff) untuk rujukan sitasi akademik.
