# Smart Marine Monitoring Buoy (SMMB)

**Prototipe Buoy Pemantau Kualitas Air Laut Berbasis IoT & Data Science**  
*Institut Teknologi Sepuluh Nopember (ITS), Surabaya · 2026–2027*

---

## 📁 Struktur Repositori

```text
smart-buoy/
├── dashboard/               # Web Dashboard Streamlit (Python)
│   ├── app.py               # Aplikasi utama (Overview, Tren, Peta, Form Validasi, Export)
│   ├── requirements.txt     # Dependensi Python
│   └── .streamlit/
│       └── secrets.toml.example
├── db/                      # Skema Database & Serverless
│   ├── schema.sql           # Skema lengkap PostgreSQL (Tabel, Enum, Trigger, Views, QC)
│   └── supabase/functions/
│       ├── ingest/index.ts         # Edge Function penerima payload ESP32
│       └── notify-telegram/index.ts # Edge Function pengirim alarm ke Telegram
├── firmware/                # Kode ESP32 (Arduino Framework)
│   └── esp32_smmb/
│       ├── esp32_smmb.ino   # Firmware siklus deep sleep, sensor, microSD & 4G
│       └── config.h.example # Konfigurasi PIN, APN, dan Endpoint Supabase
├── PRD Smart Marine Monitoring Buoy (SMMB) v1.1 (2).md
├── SMMB_ERD_Schema.md
├── .gitignore
└── README.md
```

---

## 🚀 Panduan Setup Singkat (100% Gratis)

### 1. Inisialisasi Database di Supabase
1. Buka [supabase.com](https://supabase.com) dan buat proyek baru (*Free Tier*).
2. Masuk ke **SQL Editor** di sidebar kiri.
3. Buka file `db/schema.sql`, salin seluruh isinya, lalu jalankan (**Run**).
4. Catat **Project URL** dan **Anon/Service Role API Key** di menu `Project Settings > API`.

### 2. Menjalankan Dashboard Streamlit Secara Lokal
```bash
# 1. Masuk ke folder dashboard
cd dashboard

# 2. Buat virtual environment (opsional tapi disarankan)
python3 -m venv venv
source venv/bin/activate  # Untuk Windows: venv\Scripts\activate

# 3. Install library pendukung
pip install -r requirements.txt

# 4. Buat file secrets lokal (opsional, jika kosong dashboard otomatis mode demo)
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Isi SUPABASE_URL dan SUPABASE_KEY di file tersebut

# 5. Jalankan aplikasi
streamlit run app.py
```

### 3. Deploy Dashboard ke Streamlit Community Cloud
1. Unggah (*push*) folder ini ke akun **GitHub** Anda.
2. Buka [share.streamlit.io](https://share.streamlit.io).
3. Klik **New App**, pilih repositori Anda, branch `main`, dan path: `dashboard/app.py`.
4. Buka menu **Advanced Settings > Secrets**, masukkan:
   ```toml
   SUPABASE_URL = "https://xxxx.supabase.co"
   SUPABASE_KEY = "eyJh......"
   ```
5. Klik **Deploy**. Web monitoring Anda akan langsung online dan siap diakses secara publik.

### 4. Setup Bot Telegram untuk Alarm
1. Buat bot baru lewat **@BotFather** di Telegram untuk mendapatkan token.
2. Tambahkan bot ke grup tim peneliti / teknisi, lalu catat `chat_id`.
3. Masukkan `TELEGRAM_BOT_TOKEN` dan `TELEGRAM_CHAT_ID` ke konfigurasi Supabase Edge Function (`notify-telegram`).

### 5. Menyiapkan Firmware ESP32
1. Buka folder `firmware/esp32_smmb/` di Arduino IDE atau VS Code (PlatformIO).
2. Salin `config.h.example` menjadi `config.h`.
3. Sesuaikan URL Ingest Supabase, API Key, dan pin sensor.
4. Upload ke board ESP32.

---

## 📊 Fitur Dashboard
* **Ringkasan Live:** Metrik suhu, salinitas, turbidity, pH, dan status baterai.
* **Tren Kualitas Air:** Grafik interaktif dengan penanda Quality Control (QARTOD).
* **Peta & Geofence:** Visualisasi posisi GPS buoy terkini dengan radius batas hanyut 50 meter.
* **Validasi Lapangan:** Form khusus untuk teknisi mencatat pengukuran referensi (MPV portable / uji lab).
* **Unduh Dataset:** Ekspor langsung ke format CSV untuk analisis manuskrip ilmiah.

