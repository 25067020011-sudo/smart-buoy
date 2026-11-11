#!/usr/bin/env python3
"""
SMMB — Dataset Quality Assessment (DQA) Analysis
Mengimplementasikan metrik penilaian kualitas dataset ilmiah dari 06_DATASET_QUALITY_ASSESSMENT.md:
- Completeness (Kelengkapan)
- Validity & Suspect Rate (QC Flags)
- Uniqueness (Keunikan sequence)
- Validasi terhadap alat referensi (Bias, RMSE, R^2)
"""

import numpy as np
import pandas as pd

def calculate_dqa_metrics(df_measurements: pd.DataFrame, expected_count: int = None):
    """
    Menghitung metrik kualitas data sesuai panduan DQA SMMB v1.1.
    """
    total_records = len(df_measurements)
    if total_records == 0:
        return {"status": "No data"}

    # 1. Completeness (D1)
    if expected_count is None:
        expected_count = total_records
    completeness = min(100.0, (total_records / expected_count) * 100.0)

    # 2. Uniqueness (D3)
    duplicates = df_measurements.duplicated(subset=["device_id", "seq"]).sum()
    uniqueness = (1.0 - (duplicates / total_records)) * 100.0

    # 3. Validity & Suspect Rate (D2)
    # Parse qc_flags jika berbentuk dict atau string json
    flags = df_measurements["qc_flags"] if "qc_flags" in df_measurements else []
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

    # Penilaian Grade (A/B/C/D)
    if completeness >= 90.0 and validity >= 95.0 and suspect_rate <= 5.0:
        grade = "A (Sangat Baik / Siap Publikasi Q1)"
    elif completeness >= 80.0 and validity >= 90.0:
        grade = "B (Baik / Perlu Perhatian Minor)"
    elif completeness >= 70.0:
        grade = "C (Cukup / Butuh Kalibrasi Ulang)"
    else:
        grade = "D (Kurang / Tidak Layak Publikasi)"

    return {
        "Total Record": total_records,
        "Completeness (%)": round(completeness, 2),
        "Uniqueness (%)": round(uniqueness, 2),
        "Validity (% Flag 1)": round(validity, 2),
        "Suspect Rate (% Flag 3)": round(suspect_rate, 2),
        "Overall Grade": grade
    }

def calculate_reference_comparison(sensor_values, ref_values):
    """
    Menghitung Bias, RMSE, dan R^2 antara sensor vs instrumen referensi lab/MPV.
    """
    s = np.array(sensor_values, dtype=float)
    r = np.array(ref_values, dtype=float)

    bias = np.mean(s - r)
    rmse = np.sqrt(np.mean((s - r) ** 2))
    
    correlation_matrix = np.corrcoef(s, r)
    r_squared = correlation_matrix[0, 1] ** 2 if len(s) > 1 else 1.0

    return {
        "Bias (Mean Error)": round(bias, 3),
        "RMSE": round(rmse, 3),
        "R_squared": round(r_squared, 3)
    }

if __name__ == "__main__":
    print("SMMB Dataset Quality Assessment Tool (Ready)")
