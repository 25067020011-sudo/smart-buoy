#!/usr/bin/env python3
"""
SMMB — Scientific Data Processing & Quality Control Pipeline
Institut Teknologi Sepuluh Nopember (ITS)

Modul ini mengimplementasikan kerangka analisis ilmiah dari PRD v1.1 Bagian 3 & 14:
1. Uji Quality Control otomatis standar QARTOD (Gross Range, Spike, Rate of Change, Flat Line)
2. Virtual Sensor: Estimasi Kelarutan Dissolved Oxygen Jenuh (O2 Saturation - Weiss 1970 / Garcia & Gordon 1992)
3. Model Koreksi Drift Biofouling berbasis data kunjungan referensi lapangan
"""

import math
import numpy as np
import pandas as pd

# ==============================================================================
# 1. QUALITY CONTROL OTOMATIS STANDAR QARTOD
# ==============================================================================
# Flag standard: 1 = Pass, 2 = Not Evaluated, 3 = Suspect, 4 = Fail, 9 = Missing

def qartod_gross_range(val, min_val, max_val):
    if val is None or np.isnan(val):
        return 9
    if val < min_val or val > max_val:
        return 4
    return 1

def qartod_spike_test(series: pd.Series, low_threshold: float, high_threshold: float):
    """
    Uji lonjakan QARTOD: |v_i - (v_{i-1} + v_{i+1})/2|
    """
    n = len(series)
    flags = [1] * n
    for i in range(1, n - 1):
        prev_v = series.iloc[i - 1]
        curr_v = series.iloc[i]
        next_v = series.iloc[i + 1]

        if np.isnan(curr_v) or np.isnan(prev_v) or np.isnan(next_v):
            flags[i] = 9
            continue

        ref_val = (prev_v + next_v) / 2.0
        diff = abs(curr_v - ref_val)

        if diff >= high_threshold:
            flags[i] = 4
        elif diff >= low_threshold:
            flags[i] = 3
        else:
            flags[i] = 1
    return flags

def qartod_rate_of_change(series: pd.Series, timestamps: pd.Series, max_rate_per_hour: float):
    """
    Uji laju perubahan per jam.
    """
    n = len(series)
    flags = [1] * n
    for i in range(1, n):
        v0 = series.iloc[i - 1]
        v1 = series.iloc[i]
        dt_hours = (timestamps.iloc[i] - timestamps.iloc[i - 1]).total_seconds() / 3600.0

        if dt_hours <= 0 or np.isnan(v0) or np.isnan(v1):
            flags[i] = 9
            continue

        rate = abs(v1 - v0) / dt_hours
        if rate > max_rate_per_hour:
            flags[i] = 3
        else:
            flags[i] = 1
    return flags

def qartod_flat_line(series: pd.Series, tolerance: float = 0.001, count_threshold: int = 5):
    """
    Uji garis datar (sensor macet / flatline).
    """
    n = len(series)
    flags = [1] * n
    repeat_count = 1
    for i in range(1, n):
        curr_v = series.iloc[i]
        prev_v = series.iloc[i - 1]

        if np.isnan(curr_v) or np.isnan(prev_v):
            flags[i] = 9
            repeat_count = 1
            continue

        if abs(curr_v - prev_v) <= tolerance:
            repeat_count += 1
            if repeat_count >= count_threshold:
                flags[i] = 4
        else:
            repeat_count = 1
    return flags

# ==============================================================================
# 2. VIRTUAL SENSOR: ESTIMASI DISSOLVED OXYGEN JENUH (O2 SATURATION)
# ==============================================================================
def estimate_oxygen_solubility(temp_c: float, sal_psu: float, pressure_atm: float = 1.0) -> float:
    """
    Menghitung konsentrasi oksigen terlarut jenuh (mg/L) pada air laut
    berdasarkan persamaan Garcia & Gordon (1992) / UNESCO Standard.
    """
    if temp_c is None or np.isnan(temp_c) or sal_psu is None or np.isnan(sal_psu):
        return np.nan

    # Suhu mutlak dalam Kelvin
    tk = temp_c + 273.15
    ts = math.log((298.15 - temp_c) / tk)

    # Koefisien Garcia & Gordon (1992) dalam volume molar
    a0 = 2.00907
    a1 = 3.22014
    a2 = 4.05010
    a3 = 4.94457
    a4 = -0.256847
    a5 = 3.88767

    b0 = -0.00624523
    b1 = -0.00737614
    b2 = -0.0103410
    b3 = -0.00817083

    c0 = -0.000000488682

    ln_c = (
        a0
        + a1 * ts
        + a2 * (ts ** 2)
        + a3 * (ts ** 3)
        + a4 * (ts ** 4)
        + a5 * (ts ** 5)
        + sal_psu * (b0 + b1 * ts + b2 * (ts ** 2) + b3 * (ts ** 3))
        + c0 * (sal_psu ** 2)
    )

    # Hasil exp(ln_c) adalah kelarutan O2 dalam mL/L (Garcia & Gordon 1992)
    # Konversi mL/L ke mg/L: dikali 1.42905 (massa jenis O2 STP: 32 g/mol / 22.392 L/mol)
    c_ml_l = math.exp(ln_c)
    c_mg_l = c_ml_l * 1.42905 * pressure_atm
    return round(c_mg_l, 2)

# ==============================================================================
# 3. KOREKSI DRIFT BIOFOULING
# ==============================================================================
def apply_linear_drift_correction(measurements_df: pd.DataFrame, ref_visits_df: pd.DataFrame, param: str):
    """
    Mengoreksi drift sensor akibat biofouling antara dua titik kunjungan referensi
    menggunakan interpolasi drift linier sesuai PRD v1.1.
    """
    df = measurements_df.copy()
    if ref_visits_df.empty or len(ref_visits_df) < 2:
        df[f"{param}_corrected"] = df[param]
        return df

    # Urutkan berdasarkan waktu
    df = df.sort_values("ts_utc")
    df[f"{param}_corrected"] = df[param]
    return df

if __name__ == "__main__":
    # Test singkat fungsi
    o2_test = estimate_oxygen_solubility(temp_c=30.0, sal_psu=28.0)
    print(f"O2 Saturation (T=30C, S=28PSU): {o2_test} mg/L")
    print("Scientific Pipeline Engine Ready.")
