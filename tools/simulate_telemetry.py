#!/usr/bin/env python3
"""
SMMB Buoy Telemetry Simulator
Script pengujian pengiriman data telemetri tiruan ke Supabase Edge Function / Database.
Bisa digunakan sebelum hardware buoy selesai dirakit.
"""

import argparse
import datetime
import json
import math
import random
import sys
import time

try:
    import requests
except ImportError:
    print("Modul 'requests' belum terinstall. Install dengan: pip install requests")
    sys.exit(1)

DEFAULT_DEVICE_ID = "SMMB-01"
DEFAULT_KEY = "secret123"

def generate_sample_record(device_id: str, seq: int, anchor_lat=-7.31820, anchor_lon=112.82750):
    now = datetime.datetime.now(datetime.timezone.utc)
    hour = now.hour + now.minute / 60.0

    # Simulasi siklus harian suhu & pasang surut
    temp = round(29.5 + 1.8 * math.sin(2 * math.pi * (hour - 10) / 24) + random.gauss(0, 0.15), 2)
    sal = round(28.0 + 3.5 * math.cos(2 * math.pi * (hour - 4) / 12.4) + random.gauss(0, 0.2), 2)
    turb = round(max(5.0, 25.0 + 10.0 * (math.sin(2 * math.pi * hour / 12.4) ** 2) + random.expovariate(0.3)), 2)
    ph = round(7.9 + 0.3 * math.sin(2 * math.pi * (hour - 12) / 24) + random.gauss(0, 0.05), 2)
    batt = round(12.8 + random.uniform(-0.1, 0.1), 2)

    # Pergerakan kecil di sekitar anchor (radius 5-25m)
    r = random.uniform(5, 25)
    theta = random.uniform(0, 2 * math.pi)
    lat = round(anchor_lat + (r * math.cos(theta)) / 111000.0, 5)
    lon = round(anchor_lon + (r * math.sin(theta)) / (111000.0 * math.cos(math.radians(anchor_lat))), 5)

    return {
        "device_id": device_id,
        "seq": seq,
        "ts": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "temp_c": temp,
        "ec_mscm": round(sal / 0.65, 2),
        "sal_psu": sal,
        "turb_ntu": turb,
        "ph": ph,
        "do_mgl": None,
        "lat": lat,
        "lon": lon,
        "gps_fix": True,
        "batt_v": batt,
        "solar_v": 17.5,
        "encl_temp_c": 34.2,
        "encl_rh": 60.5,
        "leak": False,
        "rssi": -78,
        "fw": "1.0.0"
    }

def main():
    parser = argparse.ArgumentParser(description="Simulate SMMB Buoy Telemetry Transmission")
    parser.add_argument("--url", type=str, help="Supabase Ingest Edge Function URL")
    parser.add_argument("--key", type=str, default=DEFAULT_KEY, help="Device API key (default: secret123)")
    parser.add_argument("--count", type=int, default=1, help="Number of records to generate & send")
    parser.add_argument("--interval", type=int, default=2, help="Interval between sends in seconds")
    parser.add_argument("--dry-run", action="store_true", help="Print payload without sending")

    args = parser.parse_args()

    seq = int(time.time()) % 100000

    print("=" * 60)
    print(f"🌊 SMMB Buoy Telemetry Simulator — Device: {DEFAULT_DEVICE_ID}")
    print("=" * 60)

    for i in range(args.count):
        record = generate_sample_record(DEFAULT_DEVICE_ID, seq + i)
        payload = [record]

        print(f"\n[Siklus #{i+1}/{args.count} - Seq: {record['seq']}]")
        print(f"Data: Suhu={record['temp_c']}°C, Salinitas={record['sal_psu']} PSU, Turbidity={record['turb_ntu']} NTU, Baterai={record['batt_v']}V")

        if args.dry_run or not args.url:
            print("Payload JSON:")
            print(json.dumps(payload, indent=2))
            if not args.url and not args.dry_run:
                print("⚠️ Gunakan argumen --url <https://xxx.supabase.co/functions/v1/ingest> untuk mengirim ke Supabase.")
        else:
            headers = {
                "Content-Type": "application/json",
                "x-device-key": args.key,
            }
            try:
                res = requests.post(args.url, headers=headers, json=payload, timeout=10)
                print(f"Status Response: {res.status_code}")
                print(f"Response Body: {res.text}")
            except Exception as e:
                print(f"❌ Gagal mengirim: {e}")

        if i < args.count - 1:
            time.sleep(args.interval)

if __name__ == "__main__":
    main()

