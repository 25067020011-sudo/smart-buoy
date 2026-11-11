# SMMB — SOP Kalibrasi & Validasi Sensor Kualitas Air
**Smart Marine Monitoring Buoy · Institut Teknologi Sepuluh Nopember (ITS)**

Dokumen ini memuat Standar Operasional Prosedur (SOP) kalibrasi sensor otomatis di laboratorium dan protokol validasi lapangan terhadap instrumen referensi (MPV portable / alat lab).

---

## 1. Kalibrasi Sensor di Laboratorium (Pre-Deployment)

### 1.1 Sensor Suhu (DS18B20)
* **Peralatan:** Termometer terkalibrasi standar laboratorium (akurasi ±0.1°C), wadah air isolasi (termos/water bath).
* **Prosedur:**
  1. Rendam probe DS18B20 berdampingan dengan termometer standar pada 3 titik suhu:
     * Titik dingin: ~15°C (campuran air es).
     * Titik ruang/pesisir: ~28°C (air suhu kamar).
     * Titik hangat: ~38°C (air hangat terkontrol).
  2. Tunggu 5 menit hingga pembacaan stabil.
  3. Catat offset selisih rata-rata. Kriteria lulus: selisih $\le \pm 0.5$ °C.

### 1.2 Sensor EC / Salinitas
* **Peralatan:** Larutan standar konduktivitas rentang air laut (misal standar KCl 12.88 mS/cm dan 50 mS/cm / 35 PSU), air deionisasi (DI water).
* **Prosedur:**
  1. Bilas probe dengan air DI, keringkan perlahan dengan tisu bebas serat.
  2. Celupkan ke larutan standar pertama (misal 12.88 mS/cm), catat tegangan analog ESP32.
  3. Celupkan ke larutan standar kedua (50 mS/cm), catat tegangan analog ESP32.
  4. Hitung gradien kemiringan (*slope*) dan *offset*.
  5. Masukkan koefisien kalibrasi ke tabel `calibrations` di database Supabase.

### 1.3 Sensor Turbidity (Kekeruhan)
* **Peralatan:** Larutan standar Formazin Turbidity Standard (0 NTU, 20 NTU, 100 NTU, dan 400 NTU), wadah gelap anti-pantulan.
* **Prosedur:**
  1. Pastikan optik sensor bersih dari goresan atau debu.
  2. Pengukuran wajib dilakukan dalam wadah gelap kedap cahaya untuk mencegah bias cahaya sekitar (*ambient light*).
  3. Buat kurva fitting polinomial kuadratik ($NTU = aV^2 + bV + c$) dari pembacaan voltase vs nilai standar Formazin.

### 1.4 Sensor pH (Submersible)
* **Peralatan:** Larutan buffer standar pH 4.01, pH 7.00, dan pH 10.01.
* **Prosedur 3-Point Calibration:**
  1. Bersihkan elektroda dengan air DI.
  2. Celupkan elektroda ke larutan buffer pH 7.00 (neutral point), tunggu stabil, sesuaikan *offset*.
  3. Celupkan ke buffer pH 4.01 (acidic point), hitung slope asam.
  4. Celupkan ke buffer pH 10.01 (alkaline point), hitung slope basa.
  5. Simpan catatan kalibrasi ke tabel `calibrations`.

---

## 2. Protokol Validasi Lapangan (Field Validation)

Kunjungan lapangan berkala dilakukan setiap **1–2 minggu** oleh tim teknisi:

1. **Pemeriksaan Fisik & Pembersihan (Biofouling):**
   * Angkat kurungan pelindung sensor dari air laut.
   * Ambil foto kondisi biofouling sensor sebelum dibersihkan (beri skor 0 = bersih, hingga 4 = tertutup penuh organisme).
   * Bersihkan probe secara perlahan menggunakan sikat lembut dan air tawar.

2. **Pengukuran Referensi Serentak (Co-located Sampling):**
   * Nyalakan instrumen multiparameter referensi (MPV portable AZ Instrument 84051 / Lutron WAC-2019SD).
   * Celupkan probe MPV pada kedalaman yang sama (±0.5 meter) dan posisi sedekat mungkin dengan sensor buoy.
   * Ambil data referensi dalam rentang waktu $\pm 5$ menit dari jadwal pencatatan buoy.

3. **Input Data ke Dashboard:**
   * Buka tab **"🔬 Kunjungan & Validasi MPV"** pada Dashboard Streamlit.
   * Masukkan nilai suhu, salinitas, turbidity, pH, dan DO dari alat referensi.
   * Sistem Supabase akan secara otomatis mencocokkan record referensi dengan record buoy terdekat (`matched_measurement_id`) untuk menghitung Bias dan RMSE.
