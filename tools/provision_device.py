#!/usr/bin/env python3
"""
SMMB Device Provisioning Tool
Membuat kredensial aman untuk unit buoy baru:
1. Menghasilkan API Key acak 32-byte berkekuatan kriptografis
2. Menghitung hash SHA-256 untuk disimpan di database Supabase (tabel devices)
3. Menghasilkan snippet config.h siap flash untuk firmware ESP32
4. Menghasilkan perintah SQL INSERT yang aman
"""

import argparse
import hashlib
import os
import secrets
import sys

def provision_new_device(device_id: str, name: str, anchor_lat: float, anchor_lon: float, geofence_m: int = 50):
    # Buat API key acak 32 bytes (64 karakter hex)
    raw_key = secrets.token_hex(32)
    key_hash = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    sql_statement = f"""
-- Pendaftaran perangkat baru: {device_id}
INSERT INTO devices (
    device_id, name, status, anchor_lat, anchor_lon, geofence_m, interval_min, batt_low_v, api_key_hash
) VALUES (
    '{device_id}',
    '{name}',
    'testing',
    {anchor_lat},
    {anchor_lon},
    {geofence_m},
    15,
    11.80,
    '{key_hash}'
) ON CONFLICT (device_id) DO UPDATE SET
    name = EXCLUDED.name,
    anchor_lat = EXCLUDED.anchor_lat,
    anchor_lon = EXCLUDED.anchor_lon,
    geofence_m = EXCLUDED.geofence_m,
    api_key_hash = EXCLUDED.api_key_hash;
""".strip()

    header_config = f"""
// ==========================================
// KREDENSIAL RAHASIA UNTUK {device_id}
// JANGAN COMMIT FILE INI KE GITHUB!
// ==========================================
#define DEVICE_ID           "{device_id}"
#define DEVICE_API_KEY      "{raw_key}"
""".strip()

    return {
        "device_id": device_id,
        "api_key": raw_key,
        "key_hash": key_hash,
        "sql": sql_statement,
        "config_snippet": header_config
    }

def main():
    parser = argparse.ArgumentParser(description="Provision a new SMMB buoy device")
    parser.add_argument("--id", type=str, default="SMMB-01", help="Device ID (misal: SMMB-01)")
    parser.add_argument("--name", type=str, default="Buoy Wonorejo ITS", help="Nama perangkat")
    parser.add_argument("--lat", type=float, default=-7.31820, help="Anchor latitude")
    parser.add_argument("--lon", type=float, default=112.82750, help="Anchor longitude")
    parser.add_argument("--geofence", type=int, default=50, help="Geofence radius in meters")
    parser.add_argument("--out-config", type=str, help="Path file output config.h untuk ESP32")

    args = parser.parse_args()

    res = provision_new_device(args.id, args.name, args.lat, args.lon, args.geofence)

    print("=" * 70)
    print(f"⚓ SMMB Device Provisioning — Unit: {res['device_id']}")
    print("=" * 70)
    print(f"🔑 Generated API Key : {res['api_key']}")
    print(f"🔒 SHA-256 Key Hash  : {res['key_hash']}")
    print("\n📋 Salin dan jalankan SQL berikut di Supabase SQL Editor:")
    print("-" * 70)
    print(res["sql"])
    print("-" * 70)

    if args.out_config:
        with open(args.out_config, "w", encoding="utf-8") as f:
            f.write(res["config_snippet"] + "\n")
        print(f"\n✅ File konfigurasi rahasia berhasil ditulis ke: {args.out_config}")
    else:
        print("\n💡 Tip: Jalankan dengan argumen --out-config firmware/esp32_smmb/config.h")
        print("   untuk langsung membuat file header ESP32 secara otomatis.")

if __name__ == "__main__":
    main()
