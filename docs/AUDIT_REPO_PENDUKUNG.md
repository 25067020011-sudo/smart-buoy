# Laporan Audit Repositori Pendukung SMMB

Dibuat: 2026-11-11 23:46 · Jumlah repo: 10

## 1. Ringkasan Kesiapan & Lisensi

| # | Repo | Lisensi | Copyleft | Paten eksplisit | Commit | Tgl commit | Test | CI | Sitasi | Skor |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `ioos/ioos_qc` | Apache-2.0 | tidak | ✓ | `524de971db61` | 2026-11-05 | ✓ | ✓ | — | **86** |
| 2 | `TEOS-10/GSW-Python` | GSW (permisif, mirip BSD) | tidak | — | `a1cc49ae9636` | 2026-11-10 | ✓ | ✓ | — | **86** |
| 3 | `wesleybowman/UTide` | MIT | tidak | — | `c46e17c9b0d6` | 2026-10-28 | ✓ | ✓ | — | **90** |
| 4 | `OceanographyforEveryone/OpenCTD` | MIT | tidak | — | `b74b3ace812c` | 2026-06-20 | — | — | — | **68** |
| 5 | `Atlas-Scientific/Ezo_I2c_lib` | MIT | tidak | — | `5140af60b780` | 2026-03-06 | — | — | — | **58** |
| 6 | `DFRobot/DFRobot_PH` | MIT | tidak | — | `43f229a843b8` | 2023-11-14 | — | — | — | **50** |
| 7 | `supabase/supabase` | Apache-2.0 | tidak | ✓ | `3f03e5b0d584` | 2026-11-11 | ✓ | ✓ | — | **84** |
| 8 | `streamlit/streamlit` | Apache-2.0 | tidak | ✓ | `2488e4724c76` | 2026-11-11 | ✓ | ✓ | — | **80** |
| 9 | `ioos/erddapy` | BSD-3-Clause | tidak | — | `cb023fb342fc` | 2026-11-10 | ✓ | ✓ | — | **94** |
| 10 | `sentinel-hub/sentinelhub-py` | MIT | tidak | — | `b466167df34d` | 2026-11-06 | ✓ | ✓ | — | **94** |

---

## 2. Rincian per Repositori untuk Naskah Ilmiah (Code Availability)

### 2.1 ioos/ioos_qc
* **Fungsi:** Uji otomatis Quality Control QARTOD (gross range, spike, rate of change, flat line).
* **Lisensi:** Apache-2.0 (`LICENSE.txt`)
* **Versi Terkunci:** commit `524de971db61` (tag `v3.1.1`).
* **Kutipan Jurnal:** `ioos/ioos_qc (commit 524de971db61, 2026-11-05), https://github.com/ioos/ioos_qc, lisensi Apache-2.0.`

### 2.2 TEOS-10/GSW-Python
* **Fungsi:** Konversi salinitas standar PSS-78/TEOS-10 dan kalkulasi kelarutan oksigen jenuh ($O_2$ saturation model).
* **Lisensi:** GSW Permissive (`LICENSE.txt`)
* **Versi Terkunci:** commit `a1cc49ae9636`.
* **Kutipan Jurnal:** `TEOS-10/GSW-Python (commit a1cc49ae9636, 2026-11-10), https://github.com/TEOS-10/GSW-Python, lisensi GSW.`

### 2.3 wesleybowman/UTide
* **Fungsi:** Analisis harmonik pasang surut komponen utama pesisir Surabaya ($M_2, S_2, K_1, O_1$).
* **Lisensi:** MIT (`LICENSE.txt`)
* **Versi Terkunci:** commit `c46e17c9b0d6` (versi 0.4.0).
* **Kutipan Jurnal:** `wesleybowman/UTide (commit c46e17c9b0d6, 2026-10-28), https://github.com/wesleybowman/UTide, lisensi MIT.`

### 2.4 OceanographyforEveryone/OpenCTD
* **Fungsi:** Rujukan desain perangkat keras pelindung probe CTD dan kompensasi konduktivitas.
* **Lisensi:** MIT (`LICENSE.md`)
* **Versi Terkunci:** commit `b74b3ace812c`.

### 2.5 Atlas-Scientific/Ezo_I2c_lib
* **Fungsi:** Driver I2C modul pembacaan sensor kualitas air laboratorium.
* **Lisensi:** MIT (`LICENSE`)
* **Versi Terkunci:** commit `5140af60b780`.

### 2.6 DFRobot/DFRobot_PH
* **Fungsi:** Pustaka kalibrasi 2-titik untuk modul analog pH.
* **Lisensi:** MIT (`LICENSE`)
* **Versi Terkunci:** commit `43f229a843b8`.

### 2.7 supabase/supabase
* **Fungsi:** Infrastruktur backend terkelola (PostgreSQL 15+, REST API PostgREST, Row Level Security, Edge Functions).
* **Lisensi:** Apache-2.0 (`LICENSE`)
* **Versi Terkunci:** commit `3f03e5b0d584`.

### 2.8 streamlit/streamlit
* **Fungsi:** Framework frontend web dashboard pemantauan interaktif.
* **Lisensi:** Apache-2.0 (`LICENSE`)
* **Versi Terkunci:** commit `2488e4724c76` (versi 1.67.0).

### 2.9 ioos/erddapy
* **Fungsi:** Pengambilan dataset oseanografi pembanding dari server ERDDAP NOAA/IOOS.
* **Lisensi:** BSD-3-Clause (`LICENSE.txt`)
* **Versi Terkunci:** commit `cb023fb342fc` (versi 3.3.2).

### 2.10 sentinel-hub/sentinelhub-py
* **Fungsi:** Ekstraksi citra satelit Sentinel-2 (L2A) untuk validasi match-up data kekeruhan (turbidity).
* **Lisensi:** MIT (`LICENSE.md`)
* **Versi Terkunci:** commit `b466167df34d` (tag `v3.12.1`).
