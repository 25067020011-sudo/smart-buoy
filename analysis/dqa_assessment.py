#!/usr/bin/env python3
"""
SMMB — Dataset Quality Assessment (DQA) Analysis Tool
Mengimplementasikan metrik penilaian kualitas dataset ilmiah dari 06_DATASET_QUALITY_ASSESSMENT.md:
- Completeness (D1) dengan perhitungan durasi deployment & interval
- Uniqueness (D3) dengan pembersihan duplikasi
- Validity & Suspect Rate (D2)
- Validasi referensi: Bias, RMSE, R^2, Bland-Altman Limits of Agreement, & Regresi Deming
"""

import numpy as np
import pandas as pd

def calculate_dqa_metrics(df_measurements: pd.DataFrame, interval_minutes: int = 15, start_time=None, end_time=None):
    """
    Menghitung metrik kelengkapan, keunikan, dan keabsahan data ilmiah SMMB.
    """
    total_raw = len(df_measurements)
    if total_raw == 0:
        return {"status": "No data"}

    # 1. Deduplikasi record (D3)
    duplicates = df_measurements.duplicated(subset=["device_id", "seq"]).sum()
    uniqueness = (1.0 - (duplicates / total_raw)) * 100.0

    # Buang duplikasi sebelum kalkulasi metrik lainnya
    df_clean = df_measurements.drop_duplicates(subset=["device_id", "seq"]).copy()
    n_rec = len(df_clean)

    # 2. Completeness (D1)
    if start_time is not None and end_time is not None:
        duration_hours = (pd.to_datetime(end_time) - pd.to_datetime(start_time)).total_seconds() / 3600.0
        n_exp = int((duration_hours * 60.0) / interval_minutes) + 1
    elif "ts_utc" in df_clean.columns and len(df_clean) > 1:
        ts_min = pd.to_datetime(df_clean["ts_utc"]).min()
        ts_max = pd.to_datetime(df_clean["ts_utc"]).max()
        duration_hours = (ts_max - ts_min).total_seconds() / 3600.0
        n_exp = max(1, int((duration_hours * 60.0) / interval_minutes) + 1)
    else:
        n_exp = max(1, n_rec)

    completeness = min(100.0, (n_rec / n_exp) * 100.0)

    # 3. Validity & Suspect Rate (D2)
    flags = df_clean.get("qc_flags", [])
    pass_count = 0
    suspect_count = 0
    fail_count = 0
    total_checks = 0

    for flag_entry in flags:
        if isinstance(flag_entry, dict):
            for param, flag in flag_entry.items():
                total_checks += 1
                if flag == 1:
                    pass_count += 1
                elif flag == 3:
                    suspect_count += 1
                elif flag == 4:
                    fail_count += 1

    validity = (pass_count / total_checks * 100.0) if total_checks > 0 else 100.0
    suspect_rate = (suspect_count / total_checks * 100.0) if total_checks > 0 else 0.0

    # Grade mutu dataset (A - D)
    if completeness >= 90.0 and validity >= 95.0 and suspect_rate <= 5.0:
        grade = "A (Siap Publikasi Jurnal Q1)"
    elif completeness >= 80.0 and validity >= 90.0:
        grade = "B (Baik / Perlu Perhatian Minor)"
    elif completeness >= 70.0:
        grade = "C (Cukup / Butuh Kalibrasi Ulang)"
    else:
        grade = "D (Kurang / Tidak Layak Publikasi)"

    return {
        "Total Raw Records": total_raw,
        "Clean Records": n_rec,
        "Expected Records": n_exp,
        "Completeness (%)": round(completeness, 2),
        "Uniqueness (%)": round(uniqueness, 2),
        "Validity (% Flag 1)": round(validity, 2),
        "Suspect Rate (% Flag 3)": round(suspect_rate, 2),
        "Overall Grade": grade
    }

def calculate_reference_comparison(sensor_values, ref_values):
    """
    Menghitung Bias, RMSE, R^2, Bland-Altman LoA, dan Regresi Deming
    sesuai Bab III Proposal Penelitian SMMB.
    """
    s = np.array(sensor_values, dtype=float)
    r = np.array(ref_values, dtype=float)

    # Filter NaN jika ada
    valid_mask = ~np.isnan(s) & ~np.isnan(r)
    s = s[valid_mask]
    r = r[valid_mask]

    if len(s) < 2:
        return {"status": "Insufficient data"}

    diff = s - r
    bias = np.mean(diff)
    sd_diff = np.std(diff, ddof=1)
    rmse = np.sqrt(np.mean(diff ** 2))

    # Bland-Altman Limits of Agreement (LoA = bias +- 1.96 * SD)
    loa_upper = bias + 1.96 * sd_diff
    loa_lower = bias - 1.96 * sd_diff

    # Korelasi Pearson & R^2
    corr = np.corrcoef(s, r)[0, 1]
    r_squared = corr ** 2

    # Regresi Deming (asumsi lambda delta = 1)
    s_xx = np.var(r, ddof=1)
    s_yy = np.var(s, ddof=1)
    s_xy = np.cov(r, s)[0, 1]
    deming_slope = (s_yy - s_xx + np.sqrt((s_yy - s_xx) ** 2 + 4 * (s_xy ** 2))) / (2 * s_xy)
    deming_intercept = np.mean(s) - deming_slope * np.mean(r)

    return {
        "Bias (Mean Error)": round(bias, 3),
        "SD Error": round(sd_diff, 3),
        "RMSE": round(rmse, 3),
        "R_squared": round(r_squared, 3),
        "Bland-Altman LoA Upper": round(loa_upper, 3),
        "Bland-Altman LoA Lower": round(loa_lower, 3),
        "Deming Slope": round(deming_slope, 3),
        "Deming Intercept": round(deming_intercept, 3)
    }

if __name__ == "__main__":
    print("SMMB DQA Analysis Engine Ready")
