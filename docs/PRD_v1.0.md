# PRODUCT REQUIREMENTS DOCUMENT (PRD)
# SMART MARINE MONITORING BUOY (SMMB)
**IoT-Based Coastal Water Quality Monitoring System – Surabaya**  
*Institusi: Institut Teknologi Sepuluh Nopember (ITS), Surabaya*  
*Kategori: Marine Technology · Environmental Monitoring · IoT · AI*  
*Status: Initial Product Requirements – Draft 1.0*  
*Target Pengembangan: 2026–2027*  
*Durasi Penelitian: 6–12 bulan*  
*Target Lokasi: Pesisir Wonorejo, Surabaya (tentatif)*  
*Target Anggaran Awal: Maksimal Rp10.000.000*  
*Anggaran MPV Second: Maksimal Rp3.000.000*  

---

## 1. PROJECT OVERVIEW

### 1.1 Nama Produk
**SMART MARINE MONITORING BUOY (SMMB)**

Sistem buoy berbasis Internet of Things (IoT) untuk melakukan pengukuran dan pemantauan kualitas air laut secara berkala, menyimpan data lingkungan, serta mengirimkan informasi ke dashboard monitoring.

Produk dirancang sebagai prototipe teknologi kelautan berbiaya rendah yang dapat dikembangkan untuk kebutuhan penelitian, pemantauan lingkungan pesisir, pendidikan, dan inovasi teknologi maritim.

### 1.2 Problem Statement
Pemantauan kualitas air laut membutuhkan pengukuran berbagai parameter secara berkala. Penggunaan alat ukur portable mengharuskan peneliti datang langsung ke lokasi untuk mengambil data.

Permasalahan yang ingin diselesaikan:
* Pengukuran kualitas air belum selalu dilakukan secara kontinu.
* Pengumpulan data manual membutuhkan waktu dan tenaga.
* Data lingkungan belum terintegrasi dalam satu dashboard.
* Perubahan kualitas air pesisir membutuhkan pemantauan jangka panjang.
* Instrumen multiparameter profesional relatif mahal untuk penelitian awal.
* Perangkat penelitian di laut memiliki risiko kerusakan, korosi, dan pencurian.

### 1.3 Product Vision
Mengembangkan stasiun monitoring kualitas air laut berbasis buoy yang ekonomis, modular, dapat dikembangkan, dan menghasilkan data penelitian yang dapat dipertanggungjawabkan secara ilmiah.

---

## 2. PRODUCT OBJECTIVES
Target utama proyek:
1. Mengembangkan satu prototipe buoy berdiameter 50–100 cm.
2. Mengintegrasikan lima parameter kualitas air.
3. Menggunakan MPV (Multiparameter Water Quality Meter) bekas yang masih layak.
4. Mengembangkan sistem IoT dan dashboard.
5. Menyimpan data pengukuran secara berkala.
6. Mengembangkan sistem GPS dan keamanan perangkat.
7. Melakukan pengujian selama 6–12 bulan.
8. Menghasilkan dataset dan publikasi ilmiah.

### 2.1 Key Performance Indicators (KPI)
| Indikator | Target |
|---|---|
| Jumlah prototipe | 1 unit |
| Diameter buoy | 80 cm |
| Parameter monitoring | 5 |
| Interval pencatatan | 10–15 menit untuk sensor otomatis |
| Durasi penelitian | 6–12 bulan |
| Data availability | Target minimal 90% |
| Dashboard | 1 aplikasi |
| Penyimpanan data | MicroSD dan cloud |
| GPS tracking | Tersedia |
| Publikasi | Minimal 1 manuskrip ilmiah |

*KPI merupakan target pengembangan, bukan hasil yang telah dicapai.*

---

## 3. PRODUCT SCOPE

### 3.1 Core Features
#### A. Water Quality Monitoring
Sistem harus dapat memantau lima parameter:
| Parameter | Fungsi | Satuan |
|---|---|---|
| pH | Mengukur keasaman air | pH |
| Dissolved Oxygen | Mengukur oksigen terlarut | mg/L |
| Salinity | Mengukur kadar garam | PSU/ppt |
| Temperature | Mengukur suhu air | °C |
| Turbidity | Mengukur kekeruhan | NTU |

*Catatan: MPV yang dibeli harus diverifikasi spesifikasi probe-nya. Apabila perangkat tidak mempunyai sensor turbidity, gunakan sensor tambahan yang dikalibrasi secara terpisah.*

#### B. IoT Monitoring
Fungsi:
* Mengambil data sensor.
* Mengirimkan data ke server.
* Menyimpan data secara lokal.
* Mengirimkan notifikasi apabila terjadi gangguan.
* Menampilkan grafik kualitas air.

#### C. GPS Tracking
Fungsi:
* Memantau koordinat buoy.
* Mendeteksi perubahan posisi.
* Memberikan peringatan ketika buoy keluar dari radius lokasi yang ditentukan.

#### D. Solar Power System
Fungsi:
* Menggunakan panel surya.
* Menyimpan energi pada baterai.
* Mengatur konsumsi listrik.
* Memantau tegangan baterai.

---

## 4. HARDWARE REQUIREMENTS

### 4.1 Buoy Structure
| Komponen | Spesifikasi |
|---|---|
| Diameter | 80 cm |
| Material | HDPE marine grade |
| Warna | Kuning/oranye |
| Enclosure | Waterproof |
| Mounting | Rangka stainless steel marine grade atau material tahan korosi |
| Mooring | Anchor, chain dan rope |
| Identitas | Nomor aset dan identitas penelitian |

### 4.2 Multiparameter Water Quality Meter
Prioritas pengadaan barang second:
* AZ Instrument 84051.
* Lutron WAC-2019SD.
* Alternatif multiparameter meter lain dengan spesifikasi yang sesuai.

Persyaratan pembelian:
* Semua probe yang dibutuhkan tersedia.
* Display berfungsi.
* Baterai dan charger tersedia.
* Sensor dapat dikalibrasi.
* Tidak ada kerusakan kabel atau konektor.
* Manual dan model produk dapat diverifikasi.
* Tersedia suku cadang probe.
* Batas harga pengadaan: Rp3.000.000.

*MPV portable menjadi alat referensi pengukuran awal. Integrasi otomatis ke buoy hanya dilakukan jika perangkat mendukung komunikasi data atau output yang dapat diakses. Jangan mengasumsikan MPV portable bisa langsung dihubungkan ke ESP32.*

### 4.3 Electronic Components
* ESP32 development board.
* MicroSD module.
* RTC module.
* GPS module.
* 4G communication module.
* Solar panel.
* Battery.
* Solar charge controller.
* Waterproof enclosure.
* Cable gland.
* Sensor turbidity tambahan.

---

## 5. SOFTWARE REQUIREMENTS

### 5.1 System Architecture
Arsitektur sistem:  
`Water Quality Sensor → ESP32 → Data Logger → Internet Gateway → Cloud Database → Dashboard`

### 5.2 Technology Stack
| Layer | Teknologi |
|---|---|
| Microcontroller | ESP32 |
| Firmware | Arduino IDE / C++ |
| Communication | MQTT / HTTP |
| Database | Supabase / Firebase |
| Backend | Python / FastAPI |
| Dashboard | React / Grafana |
| Data Analysis | Python / Pandas |
| Visualization | Plotly |
| Mapping | Leaflet / OpenStreetMap |

### 5.3 Dashboard Features
Dashboard harus memiliki:
* Live monitoring.
* Grafik pH, DO, salinitas, suhu, turbidity.
* Status perangkat & baterai.
* Lokasi GPS & riwayat pengukuran.
* Download CSV.
* Alarm gangguan.

### 5.4 User Roles
| Pengguna | Hak akses |
|---|---|
| Administrator | Pengelolaan sistem |
| Researcher | Melihat dan mengunduh data |
| Supervisor | Memantau hasil penelitian |
| Technician | Memantau status alat dan pemeliharaan |

---

## 6. SYSTEM SECURITY REQUIREMENTS
Keamanan menjadi bagian penting karena buoy akan ditempatkan di perairan terbuka.  
Persyaratan:
* GPS tracking & alarm perubahan posisi.
* Nomor inventaris ITS & identitas kontak peneliti.
* Enclosure terkunci.
* Sistem tambatan yang dirancang sesuai kondisi perairan.
* Backup data lokal.
* Pemeriksaan kondisi perangkat berkala.
* Kerja sama pengawasan dengan mitra masyarakat pesisir.

---

## 7. LOCATION REQUIREMENTS
* **Primary Candidate:** Wonorejo, Surabaya (Ekosistem mangrove/estuari, variasi salinitas dan turbidity tinggi).
* **Alternative Candidate:** Tambak Wedi, Kenjeran (Aktivitas perikanan dan pengawasan nelayan).

---

## 8. BUDGET REQUIREMENTS
Target anggaran maksimal Rp10 juta.

| Komponen | Estimasi |
|---|---|
| MPV second | Rp3.000.000 |
| Sensor turbidity tambahan | Rp250.000 |
| ESP32 dan modul | Rp350.000 |
| GPS dan komunikasi | Rp400.000 |
| Panel surya | Rp300.000 |
| Baterai | Rp400.000 |
| Buoy HDPE | Rp850.000 |
| Mooring system | Rp750.000 |
| Enclosure waterproof | Rp350.000 |
| Kabel dan konektor | Rp350.000 |
| Kalibrasi dan pengujian | Rp500.000 |
| Instalasi dan transportasi | Rp700.000 |
| Cadangan | Rp500.000 |
| **TOTAL** | **Rp8.700.000** |

---

## 9. DEVELOPMENT ROADMAP
1. **Phase 1:** Requirement & feasibility study
2. **Phase 2:** Procurement
3. **Phase 3:** Prototype development
4. **Phase 4:** Hardware integration
5. **Phase 5:** Software development
6. **Phase 6:** Laboratory testing
7. **Phase 7:** Field testing
8. **Phase 8:** Long-term monitoring
9. **Phase 9:** Data analysis
10. **Phase 10:** Publication (manuskrip ilmiah)

Target pelaksanaan: 6–12 bulan.

---

## 10. EXPECTED DELIVERABLES
* Satu unit Smart Marine Monitoring Buoy.
* Satu sistem IoT.
* Satu dashboard monitoring.
* Dataset kualitas air pesisir.
* Dokumentasi kalibrasi & teknis.
* Laporan penelitian & manuskrip ilmiah.
* Dokumentasi potensi HKI.
