# SMMB — Dataset Quality Assessment (DQA)

**Smart Marine Monitoring Buoy · kerangka penilaian kualitas dataset · v1.1**

Dokumen ini menetapkan **cara menilai kualitas dataset SMMB**: dimensi kualitas, rumus metrik, ambang lulus, sistem grade, analisis validasi dan drift, anggaran ketidakpastian, format laporan, dan kesiapan rilis dataset untuk publikasi Q1.

Rujukan: `01_PRD.md` (Bagian 3, 7.5, 11, 14) · `02_ERD_SCHEMA.md` (tabel `measurements`, `reference_measurements`, view `v_validation_pairs`) · `05_RULES.md` (Bagian 6)

> Status: kerangka disusun sebelum data lapangan tersedia. Ambang dan toleransi adalah target awal dan disesuaikan dengan spesifikasi sensor serta hasil uji lab.

---

## 1. Tujuan

1. Menilai apakah data SMMB **layak dipakai** untuk analisis ilmiah, per parameter dan per bulan.
2. Memberi **bukti kualitas yang dapat diaudit** reviewer jurnal: kelengkapan, akurasi terhadap referensi, drift, dan ketidakpastian.
3. Menjadi dasar **gap penelitian G1, G2, G3, G6, G7** (PRD Bagian 14).
4. Menghasilkan **laporan bulanan otomatis** dan **ringkasan akhir** untuk lampiran manuskrip dan dataset rilis.

### Kapan DQA dijalankan

| Waktu | Cakupan | Output |
|---|---|---|
| Setiap hari (otomatis) | QC per record (flag 1/2/3/4/9) | Flag di `measurements.qc_flags` |
| Setiap kunjungan lapangan | Validasi sensor vs referensi | Pasangan di `v_validation_pairs` |
| Setiap akhir bulan | Metrik + grade per parameter | Laporan DQA bulanan (Bagian 9) |
| Akhir penelitian | Seluruh periode | Ringkasan DQA + dataset rilis (Bagian 10) |

---

## 2. Dimensi Kualitas

| # | Dimensi | Pertanyaan | Sumber data |
|---|---|---|---|
| D1 | **Completeness** (kelengkapan) | Berapa persen data yang seharusnya ada benar-benar ada? | `measurements` |
| D2 | **Validity** (keabsahan) | Berapa persen data lolos QC otomatis? | `qc_flags` |
| D3 | **Uniqueness** (keunikan) | Adakah record ganda? | `(device_id, seq)` |
| D4 | **Timeliness** (ketepatan waktu) | Berapa lama data sampai ke server? Apakah jam perangkat akurat? | `ts_utc`, `received_at` |
| D5 | **Continuity** (kontinuitas) | Berapa banyak dan berapa lama celah data? | selisih `ts_utc` |
| D6 | **Accuracy** (akurasi) | Seberapa dekat sensor dengan alat referensi? | `v_validation_pairs` |
| D7 | **Precision** (presisi) | Seberapa stabil bacaan saat kondisi stabil? | uji lab, sampel berulang |
| D8 | **Stability** (stabilitas / drift) | Seberapa cepat sensor menyimpang setelah kalibrasi? | pasangan validasi + umur kalibrasi |
| D9 | **Consistency** (konsistensi) | Apakah antar-parameter masuk akal secara fisik? | EC, suhu, salinitas |
| D10 | **Traceability** (ketertelusuran) | Bisakah setiap nilai dilacak ke firmware & kalibrasinya? | `fw_version`, `calib_ids` |
| D11 | **Representativeness** (keterwakilan) | Apakah data mencakup semua fase pasang surut, siang/malam, dan musim? | `ts_utc` + data pasang surut |
| D12 | **Uncertainty** (ketidakpastian) | Berapa ± ketidakpastian setiap nilai? | anggaran ketidakpastian (Bagian 6) |

---

## 3. Metrik, Rumus, dan Ambang

Notasi: Δt = interval pencatatan (default 15 menit) · N<sub>exp</sub> = jumlah record yang dijadwalkan · N<sub>rec</sub> = jumlah record unik yang diterima dengan nilai tidak kosong.

| Dimensi | Metrik | Rumus | Target |
|---|---|---|---|
| D1 | Completeness | C = N<sub>rec</sub> / N<sub>exp</sub>, dengan N<sub>exp</sub> = (durasi deployment dalam bulan itu / Δt) + 1 | ≥ 90 % |
| D2 | Validity | V = jumlah flag 1 / N<sub>rec</sub> | ≥ 95 % |
| D2 | Suspect rate | jumlah flag 3 / N<sub>rec</sub> | ≤ 5 % |
| D3 | Uniqueness | U = 1 − (record ganda / total record) | = 100 % setelah deduplikasi |
| D4 | Latensi | median dan persentil-95 dari (`received_at` − `ts_utc`) | p50 ≤ 5 menit |
| D4 | Drift jam | selisih RTC vs GPS per hari | ≤ 2 detik/hari |
| D5 | Celah | jumlah selisih antar-record > 2Δt; celah terpanjang (jam) | celah terpanjang ≤ 24 jam |
| D6 | Bias | b = mean(s<sub>i</sub> − r<sub>i</sub>) | \|b\| ≤ ½ toleransi |
| D6 | MAE | mean(\|s<sub>i</sub> − r<sub>i</sub>\|) | ≤ toleransi |
| D6 | RMSE | √mean((s<sub>i</sub> − r<sub>i</sub>)²) | ≤ toleransi |
| D6 | R² | korelasi Pearson² antara s dan r | ≥ 0,90 |
| D6 | Limits of agreement | b ± 1,96·SD(s − r) (Bland–Altman) | di dalam ± toleransi |
| D6 | Within tolerance | proporsi pasangan dengan \|s − r\| ≤ toleransi | ≥ 90 % |
| D7 | Repeatability | SD bacaan pada larutan standar stabil (uji lab, ≥ 30 bacaan) | ≤ ⅓ toleransi |
| D8 | Laju drift | kemiringan regresi (s − r) terhadap hari sejak kalibrasi | dilaporkan; menentukan interval kalibrasi |
| D9 | Konsistensi salinitas | \|salinitas tersimpan − salinitas dihitung ulang dari EC & suhu (PSS-78)\| | ≤ 0,05 PSU |
| D10 | Traceability | proporsi record dengan `fw_version` dan `calib_ids` terisi | 100 % |
| D11 | Cakupan pasang surut | jumlah record per fase (pasang, surut, naik, turun) | tiap fase ≥ 15 % |
| D12 | Ketidakpastian diperluas | U = 2·u<sub>c</sub> (k = 2, ±95 %) | dilaporkan per parameter |

s = nilai sensor, r = nilai referensi, i = pasangan validasi ke-i (dicocokkan ±5 menit, PRD 3.4).

### 3.1 Toleransi akurasi per parameter

Sama dengan acceptance criteria PRD 11.1.

| Parameter | Kolom | Toleransi |
|---|---|---|
| Suhu | `temp_c` | ± 0,5 °C |
| Salinitas | `sal_psu` | ± 1,0 PSU |
| Turbidity | `turb_ntu` | ± 5 NTU atau ± 10 % dari referensi (ambil yang lebih besar) |
| pH | `ph` | ± 0,2 |
| DO | `do_mgl` | ± 0,5 mg/L (sesuaikan dengan spesifikasi alat referensi) |

---

## 4. Sistem Grade

Setiap kombinasi **parameter × bulan** mendapat satu grade.

| Grade | Arti | Syarat (semua harus terpenuhi) | Pemakaian |
|---|---|---|---|
| **A** | Kualitas riset | C ≥ 90 %, V ≥ 95 %, n validasi ≥ 3, \|bias\| ≤ ½ toleransi, RMSE ≤ toleransi | Analisis utama & publikasi |
| **B** | Layak dengan catatan | C ≥ 80 %, V ≥ 90 %, n validasi ≥ 3, RMSE ≤ 1,5 × toleransi | Analisis; batasan disebutkan di paper |
| **C** | Indikatif | C ≥ 60 %, V ≥ 75 % (validasi belum cukup) | Tren kualitatif saja |
| **D** | Tidak layak | Di bawah syarat C | Tidak dipakai; dicatat penyebabnya |

Catatan:

- Tanpa minimal 3 pasangan validasi dalam bulan itu, grade maksimum adalah **C**, karena akurasi belum terbukti.
- Untuk MVP, DO diukur manual (PRD Bagian 3). DO dinilai hanya dari pengukuran referensi dan, jika dibuat, dari akurasi model *virtual DO* (gap G4).

---

## 5. Validasi & Analisis Drift

### 5.1 Protokol pasangan data

1. Ukur referensi di kedalaman sensor, dalam ±5 menit dari jadwal record buoy.
2. Catat di dashboard (Maintenance → Pengukuran referensi). Sistem otomatis mencocokkan `matched_measurement_id`.
3. Catat **sebelum dan sesudah pembersihan** jika memungkinkan. Selisih sebelum–sesudah = efek fouling langsung (bukti kuat untuk G2).
4. Catat skor fouling (0–4) dan foto standar.

### 5.2 Analisis yang dilaporkan

| Analisis | Metode | Untuk gap |
|---|---|---|
| Kesesuaian sensor–referensi | Scatter + garis 1:1, bias, RMSE, R², Bland–Altman | G1 |
| Laju drift | Regresi (s − r) terhadap hari sejak kalibrasi, per parameter | G2 |
| Pengaruh fouling | Regresi/ANOVA (s − r) terhadap skor fouling; uji sebelum vs sesudah pembersihan | G2 |
| Koreksi drift | Interpolasi linear offset antar-kunjungan vs model regresi; dinilai dengan leave-one-visit-out cross-validation | G3 |
| Interval kalibrasi optimal | Hari sampai drift mencapai toleransi = toleransi / laju drift | G2, G3 |

### 5.3 Contoh perhitungan interval kalibrasi

Jika laju drift salinitas = 0,02 PSU/hari dan toleransi = 1,0 PSU, maka sensor keluar toleransi setelah ± 50 hari. Dengan margin keamanan 50 %, kalibrasi dijadwalkan setiap **± 25 hari**.

---

## 6. Anggaran Ketidakpastian

Mengikuti kerangka GUM (*Guide to the Expression of Uncertainty in Measurement*). Ketidakpastian standar gabungan:

u<sub>c</sub> = √( u<sub>std</sub>² + u<sub>cal</sub>² + u<sub>rep</sub>² + u<sub>drift</sub>² + u<sub>temp</sub>² + u<sub>res</sub>² )

Ketidakpastian diperluas: **U = k · u<sub>c</sub>**, dengan k = 2 (± 95 %).

| Komponen | Sumber | Cara memperoleh |
|---|---|---|
| u<sub>std</sub> | Larutan standar kalibrasi | Sertifikat larutan (bagi √3 jika distribusi persegi) |
| u<sub>cal</sub> | Residual fit kalibrasi | SD residual kurva kalibrasi |
| u<sub>rep</sub> | Repeatability sensor | SD ≥ 30 bacaan pada larutan stabil (uji lab) |
| u<sub>drift</sub> | Drift antar-kalibrasi | (laju drift × interval kalibrasi) / √3 |
| u<sub>temp</sub> | Sisa kompensasi suhu | Uji standar pada 2 suhu (PRD 11.1) |
| u<sub>res</sub> | Resolusi ADC/tampilan | resolusi / √12 |

### Template tabel (diisi setelah uji lab)

| Komponen | Suhu (°C) | Salinitas (PSU) | Turbidity (NTU) | pH |
|---|---|---|---|---|
| u<sub>std</sub> | | | | |
| u<sub>cal</sub> | | | | |
| u<sub>rep</sub> | | | | |
| u<sub>drift</sub> | | | | |
| u<sub>temp</sub> | | | | |
| u<sub>res</sub> | | | | |
| **u<sub>c</sub>** | | | | |
| **U (k = 2)** | | | | |

Nilai U dirilis bersama dataset sebagai kolom atau metadata per parameter (gap G6).

---

## 7. Pemeriksaan Konsistensi & Keterwakilan

### 7.1 Konsistensi fisik

| Cek | Aturan | Tindakan jika gagal |
|---|---|---|
| Salinitas vs EC + suhu | Hitung ulang salinitas dengan PSS-78 (mis. paket `gsw`); selisih ≤ 0,05 PSU | Periksa konversi firmware/server |
| Suhu air vs suhu enclosure | Selisih ekstrem bisa berarti sensor suhu terangkat dari air | Flag 3 untuk periode tersebut |
| Telemetri vs data | Setiap `seq` di `measurements` ada pasangannya di `device_telemetry` | Investigasi firmware |
| Posisi vs geofence | Data saat buoy di luar geofence (terseret) ditinjau manual | Flag 3 atau 4 |
| Lompatan setelah pembersihan | Lompatan nilai tepat setelah kunjungan = indikasi fouling, bukan kejadian alam | Dicatat; masuk analisis drift |

### 7.2 Keterwakilan

| Aspek | Cara menilai | Target |
|---|---|---|
| Fase pasang surut | Gabungkan dengan prediksi pasang surut; hitung proporsi record per fase | Tiap fase ≥ 15 % |
| Siang / malam | Proporsi record 06–18 WIB vs 18–06 WIB | Masing-masing 40–60 % |
| Musim | Bulan musim hujan vs kemarau yang tercakup | Minimal satu bulan dari masing-masing |
| Kejadian ekstrem | Hari hujan lebat / banjir rob yang tercakup (data BMKG) | Dicatat, untuk analisis G10 |

---

## 8. Skrip DQA (Python)

Simpan sebagai `analysis/dqa.py`. Input diekspor dari Supabase:

- `measurements.csv` → kolom `device_id, seq, ts_utc, received_at, temp_c, sal_psu, turb_ntu, ph, do_mgl, fw_version, calib_ids, qc_flags`
- `reference.csv` → dari `v_validation_pairs`, ditambah kolom `days_since_calib`

Jalankan:

```bash
pip install pandas numpy
python dqa.py measurements.csv reference.csv --interval 15 --out dqa_report.csv
```

```python
"""SMMB Dataset Quality Assessment (DQA).

Input  : measurements.csv, reference.csv (export from Supabase views)
Output : per-parameter, per-month quality metrics + grade (A/B/C/D)
Usage  : python dqa.py measurements.csv reference.csv --interval 15 --out dqa_report.csv
"""
import argparse
import json
import numpy as np
import pandas as pd

# column -> (tolerance, relative_tolerance_fraction or None)
TOL = {
    "temp_c":   (0.5, None),
    "sal_psu":  (1.0, None),
    "turb_ntu": (5.0, 0.10),   # max(5 NTU, 10 % of reference)
    "ph":       (0.2, None),
    "do_mgl":   (0.5, None),   # adjust to reference instrument spec
}
PARAM = {"temp": "temp_c", "salinity": "sal_psu", "turbidity": "turb_ntu", "ph": "ph", "do": "do_mgl"}


def load(meas_path, ref_path=None):
    m = pd.read_csv(meas_path, parse_dates=["ts_utc", "received_at"])
    m["qc_flags"] = m["qc_flags"].fillna("{}").apply(json.loads)
    r = pd.read_csv(ref_path, parse_dates=["measured_at", "sensor_ts"]) if ref_path else None
    return m, r


def flag(m, col):
    return m["qc_flags"].apply(lambda f: f.get(col, 2))


def completeness(m, col, interval_min, start, end):
    """start/end: deployment window clipped to the month being assessed."""
    span_min = (end - start).total_seconds() / 60
    expected = int(span_min // interval_min) + 1
    received = m[col].notna().sum()
    return received / expected if expected else np.nan, received, expected


def validity(m, col):
    f = flag(m, col)[m[col].notna()]
    return (f == 1).mean() if len(f) else np.nan


def timeliness(m):
    lat = (m["received_at"] - m["ts_utc"]).dt.total_seconds() / 60
    return lat.median(), lat.quantile(0.95)


def gap_stats(m, interval_min):
    d = m.sort_values("ts_utc")["ts_utc"].diff().dt.total_seconds() / 60
    gaps = d[d > 2 * interval_min]
    return len(gaps), (gaps.max() / 60 if len(gaps) else 0.0)


def accuracy(r, col):
    """r: validation pairs with columns parameter, ref_value, sensor_value."""
    p = [k for k, v in PARAM.items() if v == col][0]
    x = r[r["parameter"] == p].dropna(subset=["ref_value", "sensor_value"])
    if len(x) < 2:
        return dict(n=len(x), bias=np.nan, mae=np.nan, rmse=np.nan, r2=np.nan, loa_lo=np.nan, loa_hi=np.nan, within_tol=np.nan)
    e = x["sensor_value"] - x["ref_value"]
    tol_abs, tol_rel = TOL[col]
    tol = np.maximum(tol_abs, (tol_rel or 0) * x["ref_value"].abs())
    r2 = (np.corrcoef(x["ref_value"], x["sensor_value"])[0, 1] ** 2
          if x["ref_value"].std() > 0 and x["sensor_value"].std() > 0 else np.nan)
    sd = e.std(ddof=1)
    return dict(n=len(x), bias=e.mean(), mae=e.abs().mean(), rmse=np.sqrt((e ** 2).mean()), r2=r2,
                loa_lo=e.mean() - 1.96 * sd, loa_hi=e.mean() + 1.96 * sd, within_tol=(e.abs() <= tol).mean())


def drift_rate(r, col):
    """Slope of (sensor - ref) vs days since last calibration (unit/day)."""
    p = [k for k, v in PARAM.items() if v == col][0]
    x = r[(r["parameter"] == p)].dropna(subset=["ref_value", "sensor_value", "days_since_calib"])
    if len(x) < 3:
        return np.nan
    return np.polyfit(x["days_since_calib"], x["sensor_value"] - x["ref_value"], 1)[0]


def grade(c, v, acc, col):
    tol = TOL[col][0]
    b, rm, n = acc["bias"], acc["rmse"], acc["n"]
    has_val = n >= 3 and not np.isnan(rm)
    if c >= 0.90 and v >= 0.95 and has_val and abs(b) <= tol / 2 and rm <= tol:
        return "A"
    if c >= 0.80 and v >= 0.90 and has_val and rm <= 1.5 * tol:
        return "B"
    if c >= 0.60 and v >= 0.75:
        return "C"
    return "D"


def assess(m, r, interval_min=15):
    rows = []
    m = m.copy()
    dup_rate = m.duplicated(["device_id", "seq"]).groupby(m["ts_utc"].dt.strftime("%Y-%m")).mean()
    m = m.drop_duplicates(["device_id", "seq"])          # assess unique records only
    first, last = m["ts_utc"].min(), m["ts_utc"].max()   # deployment window
    m["month"] = m["ts_utc"].dt.strftime("%Y-%m")
    if r is not None:
        r = r.copy()
        r["month"] = r["measured_at"].dt.strftime("%Y-%m")
    for month, mm in m.groupby("month"):
        rr = r[r["month"] == month] if r is not None else pd.DataFrame(columns=["parameter"])
        u = 1 - dup_rate.get(month, 0.0)
        m0 = pd.Timestamp(month + "-01", tz=mm["ts_utc"].dt.tz)
        start = max(first, m0)
        end = min(last, m0 + pd.offsets.MonthBegin(1) - pd.Timedelta(minutes=interval_min))
        lat50, lat95 = timeliness(mm)
        ngap, maxgap_h = gap_stats(mm, interval_min)
        for col in TOL:
            if col not in mm or mm[col].notna().sum() == 0:
                continue
            c, rec, exp = completeness(mm, col, interval_min, start, end)
            v = validity(mm, col)
            acc = accuracy(rr, col) if len(rr) else accuracy(pd.DataFrame(columns=["parameter", "ref_value", "sensor_value"]), col)
            dr = drift_rate(rr, col) if len(rr) and "days_since_calib" in rr else np.nan
            trace = mm.loc[mm[col].notna(), ["fw_version", "calib_ids"]].notna().all(axis=1).mean()
            rows.append(dict(month=month, parameter=col, received=rec, expected=exp,
                             completeness=round(c, 4), validity=round(v, 4), uniqueness=round(u, 4),
                             latency_p50_min=round(lat50, 1), latency_p95_min=round(lat95, 1),
                             gaps=ngap, max_gap_h=round(maxgap_h, 1), traceability=round(trace, 4),
                             **{k: (round(val, 3) if isinstance(val, float) else val) for k, val in acc.items()},
                             drift_per_day=round(dr, 4) if not np.isnan(dr) else np.nan,
                             grade=grade(c, v, acc, col)))
    return pd.DataFrame(rows)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("measurements")
    ap.add_argument("reference", nargs="?")
    ap.add_argument("--interval", type=int, default=15)
    ap.add_argument("--out", default="dqa_report.csv")
    a = ap.parse_args()
    m, r = load(a.measurements, a.reference)
    rep = assess(m, r, a.interval)
    rep.to_csv(a.out, index=False)
    print(rep.to_string(index=False))
```

### 8.1 Contoh hasil (data sintetis)

Hasil berikut berasal dari **data sintetis** 2 bulan untuk menguji skrip, termasuk gangguan sinyal 37,5 jam yang disengaja dan 5 record ganda. Ini **bukan** hasil lapangan.

| month   | parameter   |   completeness |   validity |   uniqueness |   max_gap_h |   n |   bias |   rmse |   within_tol |   drift_per_day | grade   |
|:--------|:------------|---------------:|-----------:|-------------:|------------:|----:|-------:|-------:|-------------:|----------------:|:--------|
| 2027-03 | temp_c      |         0.8901 |     1      |       0.9981 |        37.8 |   5 |  0.188 |  0.219 |            1 |          0.005  | B       |
| 2027-03 | sal_psu     |         0.8901 |     1      |       0.9981 |        37.8 |   5 |  0.07  |  0.264 |            1 |          0.0088 | B       |
| 2027-03 | turb_ntu    |         0.8901 |     0.9117 |       0.9981 |        37.8 |   5 |  1.438 |  2.076 |            1 |          0.1433 | B       |
| 2027-04 | temp_c      |         0.9434 |     1      |       1      |         0.8 |   3 | -0.033 |  0.229 |            1 |          0.0008 | A       |
| 2027-04 | sal_psu     |         0.9434 |     1      |       1      |         0.8 |   3 |  0.105 |  0.423 |            1 |         -0.0206 | A       |
| 2027-04 | turb_ntu    |         0.9434 |     0.9073 |       1      |         0.8 |   3 | -0.506 |  1.546 |            1 |          0.2534 | B       |

Cara membaca: Maret mendapat grade B karena completeness 89 % (celah 37,8 jam), di bawah syarat 90 % untuk A. Turbidity tetap B pada April karena validity 90,7 % (banyak flag suspect) dan laju drift tertinggi (±0,25 NTU/hari), yang menandakan perlunya pembersihan lebih sering.

### 8.2 Uji QC lanjutan (dijalankan di `analysis/`)

Trigger database hanya menjalankan uji *gross range*. Uji berikut dijalankan terjadwal (GitHub Actions) dan memperbarui `qc_flags`:

| Uji | Aturan awal | Flag |
|---|---|---|
| Spike | \|x<sub>t</sub> − median(x<sub>t−2..t+2</sub>)\| > k·MAD (k = 5) | 3 |
| Flat line | Nilai identik ≥ 8 record berturut-turut (2 jam) | 3; ≥ 24 record → 4 |
| Rate of change | \|Δx\| per jam > ambang per parameter | 3 |
| Pasca-kalibrasi | Periode antara dua kunjungan dengan \|s − r\| > toleransi | 3 |
| Posisi | Buoy di luar geofence | 3 |

Ambang dikalibrasi dari 30 hari data pertama dan didokumentasikan (RULES R5).

---

## 9. Template Laporan DQA Bulanan

```markdown
# Laporan DQA — SMMB-01 — <Bulan Tahun>

## Ringkasan
- Periode deployment bulan ini: <tgl> s.d. <tgl> (<n> hari)
- Grade: Suhu <A/B/C/D> · Salinitas <…> · Turbidity <…> · pH <…> · DO <…>
- Data availability keseluruhan: <x> % (target ≥ 90 %)
- Kejadian penting: <gangguan, kunjungan, kalibrasi, cuaca ekstrem>

## Tabel metrik
<tempel output dqa_report.csv untuk bulan ini>

## Validasi
- Jumlah kunjungan: <n> · pasangan validasi: <n>
- Grafik: scatter sensor vs referensi, Bland–Altman, selisih vs umur deployment

## Celah data
| Mulai (WIB) | Selesai (WIB) | Durasi | Penyebab | Tindakan |
|---|---|---|---|---|

## Tindakan bulan depan
- [ ] <mis. jadwal kalibrasi salinitas dimajukan karena drift 0,03 PSU/hari>

Disusun oleh: <nama> · Diperiksa: <supervisor> · Tanggal: <…>
```

---

## 10. Kesiapan Rilis Dataset (untuk Q1 & data paper)

### 10.1 Isi paket rilis

```
SMMB-dataset-v1.0/
├── data/
│   ├── smmb01_measurements_L1.csv     # data + flag QC (nilai asli)
│   ├── smmb01_measurements_L2.csv     # hanya grade A/B, terkoreksi drift
│   ├── smmb01_reference_pairs.csv     # pasangan validasi
│   └── smmb01_field_visits.csv        # kunjungan, skor fouling
├── docs/
│   ├── README.md                      # deskripsi, kolom, satuan, flag
│   ├── dqa_summary.md                 # ringkasan DQA seluruh periode
│   ├── uncertainty_budget.md
│   └── calibration_log.csv
├── code/                              # skrip QC, koreksi drift, DQA (versi yang dipakai)
├── LICENSE                            # mis. CC BY 4.0
└── CITATION.cff
```

**Level data**

| Level | Isi | Pengguna |
|---|---|---|
| L0 | Data mentah dari perangkat (microSD + database) | Internal, arsip |
| L1 | L0 + flag QC; nilai tidak diubah | Peneliti lain yang ingin menilai sendiri |
| L2 | L1 yang grade A/B, flag 4 dibuang, terkoreksi drift, + ketidakpastian | Analisis ilmiah |

### 10.2 Checklist FAIR

| Prinsip | Checklist |
|---|---|
| **Findable** | [ ] DOI dari repositori data (Zenodo / Mendeley Data / HuggingFace Datasets) · [ ] metadata kata kunci, lokasi (dibulatkan), periode |
| **Accessible** | [ ] Unduhan terbuka · [ ] format CSV terbuka |
| **Interoperable** | [ ] Nama kolom dengan satuan · [ ] waktu ISO 8601 UTC · [ ] flag QC mengikuti skema QARTOD (1/2/3/4/9) |
| **Reusable** | [ ] Lisensi jelas · [ ] README lengkap · [ ] kode QC & koreksi disertakan · [ ] ketidakpastian per parameter · [ ] batasan data dijelaskan |

### 10.3 Checklist sebelum submit manuskrip

- [ ] Setiap parameter yang dianalisis punya grade A atau B pada periode yang dipakai
- [ ] Tabel validasi (n, bias, RMSE, R², LoA) per parameter ada di paper
- [ ] Laju drift dan interval kalibrasi dilaporkan
- [ ] Anggaran ketidakpastian ada di lampiran
- [ ] Celah data > 24 jam dijelaskan penyebabnya
- [ ] Dataset rilis + DOI dicantumkan di Data Availability Statement
- [ ] Koordinat presisi tidak dipublikasikan
- [ ] Analisis dapat direproduksi dari `code/` (RULES R8)

---

## 11. Peran & Tanggung Jawab

| Tugas | Penanggung jawab | Frekuensi |
|---|---|---|
| Memantau flag QC & alarm | Technician | Harian |
| Input pengukuran referensi & kunjungan | Technician | Setiap kunjungan |
| Menjalankan DQA & menyusun laporan | Researcher | Bulanan |
| Meninjau dan menyetujui laporan | Supervisor | Bulanan |
| Mengubah ambang QC | Admin (atas persetujuan peneliti utama) | Bila perlu, tercatat |
| Menyusun paket rilis dataset | Researcher | Akhir penelitian |
