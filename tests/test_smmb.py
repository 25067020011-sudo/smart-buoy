import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
from analysis.dqa_assessment import calculate_dqa_metrics, calculate_reference_comparison
from analysis.scientific_pipeline import (
    estimate_oxygen_solubility,
    qartod_spike_test,
    qartod_flat_line
)
from tools.simulate_telemetry import generate_sample_record

def test_generate_sample_record():
    rec = generate_sample_record("SMMB-01", 101)
    assert rec["device_id"] == "SMMB-01"
    assert rec["seq"] == 101
    assert 20.0 <= rec["temp_c"] <= 40.0
    assert 10.0 <= rec["batt_v"] <= 15.0

def test_dqa_metrics_calculation():
    df = pd.DataFrame({
        "device_id": ["SMMB-01"] * 10,
        "seq": list(range(10)),
        "ts_utc": pd.date_range("2026-01-01", periods=10, freq="15min"),
        "qc_flags": [{"temp_c": 1}] * 10
    })
    res = calculate_dqa_metrics(df, interval_minutes=15)
    assert res["Completeness (%)"] == 100.0
    assert res["Uniqueness (%)"] == 100.0
    assert res["Validity (% Flag 1)"] == 100.0
    assert "A" in res["Overall Grade"]

def test_reference_comparison():
    sensor = [28.1, 28.5, 29.0, 29.5]
    reference = [28.0, 28.4, 29.1, 29.6]
    res = calculate_reference_comparison(sensor, reference)
    assert "Bias (Mean Error)" in res
    assert "Bland-Altman LoA Upper" in res
    assert "Deming Slope" in res
    assert res["R_squared"] > 0.9

def test_scientific_pipeline_qartod_and_do():
    # Test virtual DO
    do_sat = estimate_oxygen_solubility(30.0, 28.0)
    assert 5.0 <= do_sat <= 8.5

    # Test spike test
    series = pd.Series([28.0, 28.1, 35.0, 28.2, 28.1])
    flags = qartod_spike_test(series, low_threshold=2.0, high_threshold=5.0)
    assert flags[2] == 4 # Spiked value should fail

    # Test flat line test
    flat_series = pd.Series([28.0, 28.0, 28.0, 28.0, 28.0, 28.0])
    flat_flags = qartod_flat_line(flat_series, count_threshold=4)
    assert flat_flags[-1] == 4 # Flat line sensor stuck

