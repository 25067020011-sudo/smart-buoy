#!/usr/bin/env python3
"""
audit_smmb.py — Evaluasi & audit lengkap repositori Smart Marine Monitoring Buoy (SMMB).

Memeriksa 7 area dan menulis laporan berperingkat keparahan:
  A. Kebersihan repo & reproduktibilitas (lisensi, sitasi, test, CI, berkas duplikat/biner)
  B. Keamanan (secret bocor, kunci default, RLS Supabase, otorisasi endpoint)
  C. Integritas data ilmiah (data palsu/fallback di firmware, timestamp, nomor urut)
  D. Basis data (skema, trigger QC, view, pg_cron)                      [+ uji fungsional bila --pg]
  E. Edge Function ingest/notify
  F. Dashboard Streamlit
  G. Kode Python (pyflakes, compile) dan kesesuaian dengan PRD/proposal

Pemakaian:
  python3 audit_smmb.py /path/ke/smart-buoy
  python3 audit_smmb.py . --pg "host=/tmp port=5432 user=postgres"   # + jalankan schema.sql & uji trigger
  python3 audit_smmb.py . --out laporan/ --json                         # simpan juga JSON
  python3 audit_smmb.py . --fail-on high                                # exit code 1 bila ada temuan >= high (untuk CI)

Hanya pustaka standar. pyflakes & psql dipakai bila tersedia.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path

SEV_ORDER = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}
SEV_ICON = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵", "info": "⚪"}


@dataclass
class Finding:
    id: str
    severity: str
    area: str
    title: str
    file: str = ""
    line: int | None = None
    evidence: str = ""
    impact: str = ""
    fix: str = ""


@dataclass
class Audit:
    root: Path
    findings: list[Finding] = field(default_factory=list)
    passed: list[str] = field(default_factory=list)

    # -------- helpers --------
    def read(self, rel: str) -> str:
        p = self.root / rel
        return p.read_text(errors="ignore") if p.exists() else ""

    def exists(self, rel: str) -> bool:
        return (self.root / rel).exists()

    def find_line(self, rel: str, pattern: str) -> tuple[int | None, str]:
        for i, line in enumerate(self.read(rel).splitlines(), 1):
            if re.search(pattern, line):
                return i, line.strip()[:160]
        return None, ""

    def add(self, id, severity, area, title, file="", pattern=None, evidence="", impact="", fix=""):
        line = None
        if file and pattern:
            line, ev = self.find_line(file, pattern)
            evidence = evidence or ev
        self.findings.append(Finding(id, severity, area, title, file, line, evidence, impact, fix))

    def ok(self, msg: str):
        self.passed.append(msg)

    def files(self, *globs):
        out = []
        for g in globs:
            out += [p for p in self.root.rglob(g) if not any(x in p.parts for x in (".git", "streamlit", "supabase", "venv", ".venv", "node_modules", "audit_out"))]
        return out

    def all_files(self):
        return [p for p in self.root.rglob("*") if p.is_file() and not any(x in p.parts for x in (".git", "streamlit", "supabase", "venv", ".venv", "node_modules", "audit_out"))]
        out = []
        for g in globs:
            out += [p for p in self.root.rglob(g) if not any(x in p.parts for x in (".git", "streamlit", "supabase", "venv", ".venv", "node_modules", "audit_out"))]
        return out


# =============================================================================
# A. Kebersihan repo & reproduktibilitas
# =============================================================================
def check_repo(a: Audit):
    names = {p.name.lower() for p in a.root.iterdir()}
    if not any(n.startswith(("license", "licence", "copying")) for n in names):
        a.add("A01", "high", "Repo", "Tidak ada berkas LICENSE",
              impact="Secara hukum orang lain tidak boleh memakai/menyalin kode & data; jurnal Q1 dan "
                     "reviewer menuntut lisensi terbuka untuk 'code/data availability'.",
              fix="Tambahkan LICENSE (mis. MIT/Apache-2.0 untuk kode, CC-BY-4.0 untuk dataset & dokumen).")
    else:
        a.ok("Berkas LICENSE ada")
    if "citation.cff" not in names:
        a.add("A02", "low", "Repo", "Tidak ada CITATION.cff",
              fix="Tambahkan CITATION.cff dan arsipkan rilis di Zenodo agar mendapat DOI.")
    tests = a.files("test_*.py", "*_test.py") + [p for p in a.root.rglob("tests") if p.is_dir()]
    if not tests:
        a.add("A03", "medium", "Repo", "Tidak ada test otomatis",
              impact="Fungsi QC, DQA, dan konversi sensor tidak teruji; kesalahan rumus tidak terdeteksi.",
              fix="Tambahkan tests/ dengan pytest (DQA, simulator, konversi salinitas) dan uji SQL trigger.")
    if not (a.root / ".github" / "workflows").exists():
        a.add("A04", "low", "Repo", "Tidak ada CI (GitHub Actions)",
              fix="Workflow: pyflakes/ruff + pytest + jalankan schema.sql di service PostgreSQL.")
    # duplikat berdasarkan hash isi
    seen: dict[str, Path] = {}
    for p in a.all_files():
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        if h in seen:
            a.add("A05", "low", "Repo", "Berkas duplikat identik",
                  file=str(p.relative_to(a.root)), evidence=f"sama dengan {seen[h].relative_to(a.root)}",
                  fix="Hapus salinan (nama berakhiran ' 2', '(1)', '(2)').")
        else:
            seen[h] = p
    for p in a.all_files():
        if p.suffix.lower() in (".zip", ".rar", ".7z"):
            a.add("A06", "low", "Repo", "Arsip biner di-commit",
                  file=str(p.relative_to(a.root)),
                  fix="Jangan commit .zip; simpan dokumen sebagai berkas teks (docs/) atau lampirkan di Release.")
    bad = [p for p in a.all_files() if re.search(r"[ ()]", p.name)]
    if bad:
        a.add("A07", "low", "Repo", f"{len(bad)} nama berkas berisi spasi/kurung",
              evidence=", ".join(sorted({b.name for b in bad})[:4]),
              fix="Ganti dengan nama-pendek-tanpa-spasi, mis. docs/PRD_v1.1.md.")
    readme = a.read("README.md")
    if readme:
        for d in ("analysis", "tools", "docs"):
            if a.exists(d) and f"{d}/" not in readme:
                a.add("A08", "info", "Repo", f"Folder {d}/ tidak dijelaskan di README", file="README.md")
    req = a.read("dashboard/requirements.txt")
    if req and re.search(r">=", req) and not re.search(r"==", req):
        a.add("A09", "low", "Reproduktibilitas", "Versi dependensi tidak dikunci",
              file="dashboard/requirements.txt", pattern=">=",
              fix="Kunci versi (==) atau sertakan requirements.lock agar hasil dapat direproduksi.")


# =============================================================================
# B. Keamanan
# =============================================================================
SECRET_PATTERNS = [
    (r"eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}", "JWT / Supabase key"),
    (r"\d{8,10}:AA[A-Za-z0-9_-]{30,}", "Token bot Telegram"),
    (r"sk-[A-Za-z0-9]{20,}", "API key OpenAI"),
    (r"AKIA[0-9A-Z]{16}", "AWS access key"),
    (r"ghp_[A-Za-z0-9]{30,}", "GitHub token"),
]


def check_security(a: Audit):
    leaked = False
    for p in a.all_files():
        if p.suffix.lower() in (".zip", ".png", ".jpg", ".docx"):
            continue
        txt = p.read_text(errors="ignore")
        for pat, label in SECRET_PATTERNS:
            for m in re.finditer(pat, txt):
                leaked = True
                a.add("B01", "critical", "Keamanan", f"Kemungkinan secret bocor: {label}",
                      file=str(p.relative_to(a.root)), evidence=m.group(0)[:12] + "…",
                      fix="Cabut (revoke) kunci tersebut sekarang, hapus dari riwayat git (git filter-repo).")
    if not leaked:
        a.ok("Tidak ditemukan pola secret (JWT, token Telegram, API key) di berkas teks")
    for f in (".gitignore",):
        gi = a.read(f)
        if gi and "secrets.toml" in gi and "config.h" in gi:
            a.ok(".gitignore mengecualikan secrets.toml dan config.h")

    schema = a.read("db/schema.sql")
    if schema:
        tables = re.findall(r"create table if not exists (\w+)", schema, re.I)
        rls = set(re.findall(r"alter table (\w+) enable row level security", schema, re.I))
        missing = [t for t in tables if t not in rls]
        if missing:
            a.add("B02", "critical", "Keamanan", f"RLS tidak diaktifkan pada {len(missing)} tabel",
                  file="db/schema.sql", evidence=", ".join(missing),
                  impact="Di Supabase, tabel tanpa RLS dapat DIBACA, DIUBAH, dan DIHAPUS oleh siapa pun yang "
                         "memegang anon key — dan anon key dipakai dashboard publik. Dataset penelitian bisa "
                         "dimanipulasi tanpa jejak.",
                  fix="ALTER TABLE … ENABLE ROW LEVEL SECURITY untuk semua tabel; policy SELECT anon hanya "
                      "lewat view publik; INSERT measurements hanya via Edge Function (service role).")
        # seed hash vs kunci default yang didokumentasikan
        m = re.search(r"'([0-9a-f]{64})'\s*--\s*'([^']+)'\s*sha256", schema)
        if m:
            real = hashlib.sha256(m.group(2).encode()).hexdigest()
            if real != m.group(1):
                guess = "password" if m.group(1) == hashlib.sha256(b"password").hexdigest() else "?"
                a.add("B03", "high", "Keamanan/Fungsi", "Hash API key seed TIDAK cocok dengan kunci yang ditulis",
                      file="db/schema.sql", pattern=m.group(1)[:16],
                      evidence=f"komentar: '{m.group(2)}', hash sebenarnya = sha256('{guess}')",
                      impact="Firmware & simulator yang memakai 'secret123' akan selalu ditolak 403 oleh ingest.",
                      fix=f"Ganti dengan '{real}' — lebih baik: buat kunci acak 32 byte per perangkat, "
                          "jangan simpan di repo.")
            a.add("B04", "high", "Keamanan", "Kunci perangkat default dipublikasikan di repo",
                  file="firmware/esp32_smmb/config.h.example", pattern="DEVICE_API_KEY",
                  impact="Siapa pun dapat mengirim data palsu ke endpoint ingest bila seed dipakai saat deploy.",
                  fix="Hapus baris INSERT devices dari schema.sql produksi; buat kunci lewat skrip terpisah.")
    ingest = a.read("db/supabase/functions/ingest/index.ts")
    if ingest:
        if "length >" not in ingest and "MAX_" not in ingest:
            a.add("E01", "medium", "Edge Function", "Tidak ada batas ukuran batch",
                  file="db/supabase/functions/ingest/index.ts", pattern="Array.isArray",
                  impact="Satu request bisa berisi ribuan record (DoS / kuota Supabase habis).",
                  fix="Tolak batch > 200 record dan body > 256 KB.")
        if "Access-Control-Allow-Origin\": \"*\"" in ingest:
            a.add("E02", "info", "Edge Function", "CORS '*' pada endpoint perangkat",
                  file="db/supabase/functions/ingest/index.ts", pattern="Allow-Origin",
                  fix="Endpoint perangkat tidak butuh CORS; hapus agar tidak dipanggil dari browser.")
        if not re.search(r"timingSafeEqual|constantTime", ingest):
            a.add("E03", "low", "Edge Function", "Perbandingan hash kunci tidak constant-time",
                  file="db/supabase/functions/ingest/index.ts", pattern="api_key_hash !==")


# =============================================================================
# C. Integritas data ilmiah (firmware)
# =============================================================================
def check_firmware(a: Audit):
    fw = "firmware/esp32_smmb/esp32_smmb.ino"
    src = a.read(fw)
    if not src:
        return
    rules = [
        ("C01", "critical", r"temp_c\s*=\s*\d+\.\d+;\s*//\s*fallback",
         "Sensor suhu gagal diganti nilai tetap 29.5 °C",
         "Data palsu masuk dataset sebagai pengukuran sah; salinitas & DO jenuh ikut salah. "
         "Ini fabrikasi data bila lolos ke publikasi.",
         "Kirim null/NaN dan biarkan QC memberi flag 9 (missing)."),
        ("C02", "critical", r"data\.ph\s*=\s*\d",
         "pH tidak diukur — dikirim konstanta 8.1",
         "Seluruh deret pH di database adalah angka tetap, bukan pengukuran.",
         "Baca PIN_PH_ANALOG + kalibrasi 2 titik, atau kirim null bila sensor belum terpasang."),
        ("C03", "critical", r"gps_fix\s*=\s*true",
         "Posisi GPS hard-coded dan gps_fix selalu true",
         "Geofence tidak akan pernah terpicu walau buoy hanyut/dicuri; posisi di dataset fiktif.",
         "Baca NMEA dari modem (AT+CGPSINFO) dan set gps_fix=false bila belum lock."),
        ("C04", "critical", r"Simulasi transaksi HTTP|return true;\s*$",
         "Pengiriman 4G hanya simulasi dan selalu melapor sukses",
         "Tidak ada data yang benar-benar terkirim; kolom 'sent' di microSD tidak pernah diperbarui; "
         "store-and-forward (backlog) tidak ada.",
         "Implementasikan AT+HTTP* (SIM7600/A7670) atau TinyGSM + SSLClient; cek kode 200 dan "
         "kirim ulang baris microSD dengan sent=0."),
        ("C05", "high", r"dummy linear scale|ec_mscm \* 0\.65",
         "Konversi EC dan salinitas bukan PSS-78 dan tanpa kompensasi suhu",
         "Galat salinitas puluhan persen; tidak sesuai metode proposal (PSS-78/TEOS-10).",
         "Kirim EC mentah + suhu; hitung salinitas di server dengan gsw.SP_from_C (TEOS-10)."),
        ("C06", "high", r"RTC_DATA_ATTR uint64_t bootSequence",
         "Nomor urut (seq) disimpan di RTC RAM — reset ke 1 saat daya putus",
         "Setelah brown-out/ganti baterai, seq berulang → UNIQUE(device_id, seq) menolak data baru "
         "sebagai 'duplicate' → data hilang diam-diam.",
         "Simpan seq di NVS (Preferences) atau gunakan epoch detik sebagai seq."),
        ("C07", "high", r"buildJsonPayload",
         "Payload tidak berisi timestamp pengukuran (ts)",
         "Ingest memakai waktu server; data backlog akan bertimestamp salah — merusak analisis "
         "pasang surut & aliasing.",
         "Sertakan ts UTC dari RTC/GPS di setiap record; ingest menolak record tanpa ts."),
        ("C08", "medium", r"analogRead\(",
         "ADC ESP32 dibaca mentah tanpa koreksi non-linearitas",
         "ADC ESP32 tidak linear (terutama < 0,15 V dan > 2,5 V) → bias turbiditas & EC.",
         "Gunakan analogReadMilliVolts() + rata-rata/median N sampel; idealnya ADC eksternal ADS1115."),
        ("C09", "medium", r"PIN_PWR_SENSORS\s+12",
         "GPIO12 dipakai sebagai switch MOSFET (pin strapping)",
         "Bila GPIO12 tertarik HIGH saat boot, ESP32 memilih tegangan flash 1,8 V dan gagal boot.",
         "Pindahkan ke GPIO25/26/27 atau pastikan pull-down saat boot."),
        ("C10", "low", r"delay\(1000\)",
         "Waktu stabilisasi sensor hanya 1 detik, satu sampel per parameter",
         "Sensor EC/turbiditas/pH butuh 5–30 s; satu sampel rentan derau.",
         "Pemanasan sesuai datasheet + median dari ≥ 10 sampel (sesuai proposal Bag. 3.5.5)."),
    ]
    cfg = a.read("firmware/esp32_smmb/config.h.example")
    for rid, sev, pat, title, impact, fix in rules:
        target = fw
        hay = src
        if rid == "C09":
            target, hay = "firmware/esp32_smmb/config.h.example", cfg
        if rid == "C04":
            if "Simulasi transaksi HTTP" not in src:
                continue
            pat = "Simulasi transaksi HTTP"
        if rid == "C07":
            if '"ts' in src or "\\\"ts" in src:
                a.ok("Payload firmware berisi timestamp")
                continue
        if rid == "C06" and "Preferences" in src:
            continue
        if re.search(pat, hay, re.M):
            a.add(rid, sev, "Integritas data", title, file=target, pattern=pat, impact=impact, fix=fix)
    if "SD.begin" in src:
        a.ok("Firmware menulis salinan lokal ke microSD")
    if "esp_deep_sleep_start" in src:
        a.ok("Firmware memakai deep sleep untuk hemat daya")


# =============================================================================
# D. Basis data
# =============================================================================
def check_schema_static(a: Audit):
    s = a.read("db/schema.sql")
    if not s:
        a.add("D00", "high", "Basis data", "db/schema.sql tidak ditemukan")
        return
    for need, label in [("measurements_qc_gross_range", "trigger QC gross range"),
                        ("telemetry_before_insert", "trigger geofence/baterai/bocor"),
                        ("v_validation_pairs", "view pasangan validasi"),
                        ("unique (device_id, seq)", "deduplikasi (device_id, seq)")]:
        if need in s:
            a.ok(f"Skema memiliki {label}")
        else:
            a.add("D01", "medium", "Basis data", f"Tidak ada {label}", file="db/schema.sql")
    for test in ("spike", "rate_of_change", "flat_line"):
        if f"'{test}'" not in s.split("-- 4. VIEWS")[0].split("3. FUNCTIONS")[-1]:
            a.add("D02", "medium", "Basis data", f"Uji QARTOD '{test}' didefinisikan di enum tetapi tidak diimplementasikan",
                  file="db/schema.sql", pattern=r"create type qc_test",
                  impact="Hanya gross range yang berjalan; lonjakan & sensor macet tidak terdeteksi.",
                  fix="Implementasikan di pipeline Python (ioos_qc) terjadwal, atau trigger yang membaca N data terakhir.")
            break
    if "pg_cron" not in s and "no_data" in s:
        a.add("D03", "medium", "Basis data", "Alarm 'no_data' ada di enum tetapi tidak ada job pembuatnya",
              file="db/schema.sql", pattern="no_data",
              impact="Bila buoy mati/dicuri, tidak ada alarm 'data terhenti' — padahal ini KPI utama.",
              fix="pg_cron tiap 15 menit: INSERT alert no_data bila max(received_at) < now() - 60 menit.")
    if "calibrations" in s and "calib_ids" in s and "calib_ids" not in a.read("db/supabase/functions/ingest/index.ts"):
        a.add("D04", "low", "Basis data", "Kolom calib_ids tidak pernah diisi oleh ingest",
              file="db/schema.sql", pattern="calib_ids",
              impact="Ketertelusuran kalibrasi per data (syarat GUM/metrologi di proposal) hilang.",
              fix="Ingest mengisi calib_ids dari kalibrasi aktif (valid_to is null) per sensor.")
    if "matched_measurement_id" in s and "create or replace function match" not in s.lower():
        a.add("D05", "low", "Basis data", "Pencocokan referensi ↔ data sensor belum otomatis",
              file="db/schema.sql", pattern="matched_measurement_id",
              fix="Fungsi/trigger yang mencari record terdekat ±7,5 menit dari measured_at.")


def check_schema_live(a: Audit, dsn: str):
    psql = shutil.which("psql")
    if not psql:
        a.add("D90", "info", "Basis data", "psql tidak ditemukan — uji fungsional dilewati")
        return
    schema = a.read("db/schema.sql")
    db = "smmb_audit_" + datetime.now().strftime("%H%M%S")
    base = [psql, dsn, "-v", "ON_ERROR_STOP=1", "-q", "-X", "-At"]
    run = lambda sql, d="postgres": subprocess.run(  # noqa: E731
        base[:1] + [f"{dsn} dbname={d}"] + base[2:] + ["-c", sql], capture_output=True, text=True)
    r = run(f"create database {db}")
    if r.returncode:
        a.add("D91", "info", "Basis data", "Tidak bisa membuat database uji", evidence=r.stderr[:150])
        return
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".sql", delete=False) as f:
            f.write("create schema if not exists auth; create table if not exists auth.users(id uuid primary key);\n")
            f.write(schema)
        r = subprocess.run(base[:1] + [f"{dsn} dbname={db}"] + base[2:] + ["-f", f.name],
                           capture_output=True, text=True)
        if r.returncode:
            a.add("D10", "critical", "Basis data", "schema.sql GAGAL dijalankan", evidence=r.stderr[:200])
            return
        a.ok("schema.sql berhasil dijalankan di PostgreSQL lokal")
        q = lambda sql: run(sql, db).stdout.strip()  # noqa: E731
        q("insert into device_telemetry(device_id,seq,ts_utc,lat,lon,gps_fix,batt_v,leak) "
          "values ('SMMB-01',1,now(),-7.3190,112.8275,true,11.5,true)")
        alerts = q("select string_agg(type::text, ',' order by type) from alerts")
        (a.ok(f"Trigger telemetri membuat alarm: {alerts}") if alerts.count(",") == 2 else
         a.add("D11", "high", "Basis data", "Trigger telemetri tidak membuat 3 alarm", evidence=alerts))
        q("insert into device_telemetry(device_id,seq,ts_utc,lat,lon,gps_fix,batt_v,leak) "
          "values ('SMMB-01',2,now(),-7.3190,112.8275,true,11.5,true)")
        n = q("select count(*) from alerts")
        (a.ok("Alarm tidak dobel saat kondisi berulang") if n == "3" else
         a.add("D12", "medium", "Basis data", "Alarm dobel", evidence=f"{n} alarm"))
        q("insert into measurements(device_id,seq,ts_utc,temp_c,sal_psu,ph,turb_ntu) "
          "values ('SMMB-01',1,now(),29.5,28,5.2,30)")
        flags = q("select qc_flags->>'ph' from measurements where seq=1")
        (a.ok("QC gross range menandai pH 5,2 sebagai flag 4") if flags == "4" else
         a.add("D13", "high", "Basis data", "QC gross range tidak bekerja", evidence=f"flag pH={flags}"))
        pub = q("select count(*) from v_public_measurements")
        (a.ok("View publik menyaring data ber-flag 4") if pub == "0" else
         a.add("D14", "high", "Basis data", "View publik meloloskan data gagal QC"))
    finally:
        run(f"drop database if exists {db}")


# =============================================================================
# E/F. Edge Function & Dashboard
# =============================================================================
def check_ingest(a: Audit):
    f = "db/supabase/functions/ingest/index.ts"
    s = a.read(f)
    if not s:
        return
    if re.search(r"item\.ts\s*\|\|\s*new Date", s):
        a.add("E04", "high", "Edge Function", "Record tanpa ts diberi waktu server", file=f,
              pattern=r"item\.ts \|\|",
              impact="Data backlog dari microSD akan tercatat pada jam kirim, bukan jam ukur.",
              fix="Tolak (rejected) record tanpa ts; validasi ts tidak di masa depan > 5 menit.")
    if "records[0].device_id" in s:
        a.add("E05", "low", "Edge Function", "device_id hanya diambil dari record pertama", file=f,
              pattern=r"records\[0\]\.device_id",
              fix="Tolak batch yang berisi device_id berbeda-beda.")
    if s.count(".insert(") >= 2 and "rpc(" not in s:
        a.add("E06", "medium", "Edge Function", "Insert measurements & telemetry tidak atomik", file=f,
              pattern=r'from\("device_telemetry"\)\.insert',
              impact="Bila telemetry gagal, record dilaporkan 'rejected' → perangkat kirim ulang → "
                     "measurement dianggap duplikat dan telemetry hilang permanen.",
              fix="Satukan dalam fungsi SQL (supabase.rpc('ingest_record', …)) dalam satu transaksi.")
    if not re.search(r"typeof .*seq|Number\.isInteger", s):
        a.add("E07", "medium", "Edge Function", "Tidak ada validasi tipe/rentang nilai payload", file=f,
              pattern=r"const seq = item\.seq",
              fix="Validasi skema (zod) — seq integer ≥ 0, ts ISO-8601, angka finite.")
    n = a.read("db/supabase/functions/notify-telegram/index.ts")
    if n and 'parse_mode: "Markdown"' in n:
        a.add("E08", "low", "Edge Function", "Pesan Telegram Markdown tidak di-escape",
              file="db/supabase/functions/notify-telegram/index.ts", pattern="parse_mode",
              impact="Karakter _ * [ ` dalam pesan membuat Telegram menolak kiriman → alarm gagal terkirim.",
              fix="Pakai parse_mode HTML dengan escape, atau MarkdownV2 + escape.")
        if "res.ok" not in n:
            a.add("E09", "low", "Edge Function", "Kegagalan kirim Telegram tetap dibalas 200",
                  file="db/supabase/functions/notify-telegram/index.ts", pattern="status: 200",
                  fix="Kembalikan status non-200 bila res.ok false agar webhook mencoba ulang.")


def check_dashboard(a: Audit):
    f = "dashboard/app.py"
    s = a.read(f)
    if not s:
        return
    if re.search(r'order\("ts_utc", desc=True\)', s) and "iloc[-1]" in s and "sort_values" not in s:
        a.add("F01", "high", "Dashboard", "Data live diurutkan terbaru-dulu tetapi 'latest' = iloc[-1]",
              file=f, pattern=r"latest = df_data\.iloc\[-1\]",
              impact="Saat terhubung Supabase, kartu 'terkini' dan grafik '24 jam terakhir' menampilkan data "
                     "TERLAMA dari 500 baris (mode demo tidak terkena karena data demo urut naik).",
              fix="df = df.sort_values('ts_utc') setelah load_data().")
    if re.search(r"berhasil disimpan", s) and ".insert(" not in s:
        a.add("F02", "high", "Dashboard", "Form validasi menampilkan 'berhasil disimpan' tanpa menyimpan apa pun",
              file=f, pattern="berhasil disimpan",
              impact="Data referensi lapangan (inti RQ1–RQ3) hilang padahal teknisi mengira tersimpan.",
              fix="Insert ke field_visits + reference_measurements (butuh login & RLS), tampilkan error nyata.")
    hard = [p for p in (r"progress\(98", r'"Alarm Aktif", "0"', r'delta="Aman \(< 50m\)"', r'delta="Normal"')
            if re.search(p, s)]
    if hard:
        a.add("F03", "high", "Dashboard", f"{len(hard)} indikator ditulis tetap (hard-coded), bukan dihitung",
              file=f, pattern=hard[0],
              impact="Availability 98,4%, 'Alarm Aktif 0', dan status 'Aman' tampil walau kenyataannya berbeda — "
                     "menyesatkan pengguna dan reviewer.",
              fix="Hitung dari v_daily_availability, tabel alerts (status <> 'resolved'), dan dist_from_anchor_m.")
    if "generate_mock_data" in s and re.search(r"download_button", s) and "SIMULASI" not in s:
        a.add("F04", "critical", "Integritas data", "Mode demo mengekspor data sintetis tanpa penanda",
              file=f, pattern="download_button",
              impact="CSV data acak dapat terunduh dan terpakai seolah data lapangan → risiko fabrikasi data "
                     "tak disengaja dalam skripsi/jurnal.",
              fix="Nonaktifkan unduhan di mode demo, atau tambah kolom is_synthetic=True dan nama berkas *_SIMULASI.csv.")
    if "selected_device" in s and not re.search(r"df_data\[df_data\[.device_id.\]\s*==\s*selected_device", s):
        a.add("F05", "medium", "Dashboard", "Pilihan perangkat di sidebar tidak memfilter data",
              file=f, pattern="selected_device =")
    if "start_date" in s and not re.search(r"ts_utc.*>=.*start_date|between\(", s):
        a.add("F06", "medium", "Dashboard", "Filter tanggal unduhan tidak diterapkan",
              file=f, pattern="start_date =",
              fix="Filter df berdasarkan rentang tanggal sebelum to_csv().")
    if "QARTOD" in s and "qc_flags" in s and not re.search(r"marker.*color.*flag|flag.*color", s, re.I):
        a.add("F07", "medium", "Dashboard", "Grafik tidak menandai flag QC padahal diklaim QARTOD",
              file=f, pattern="QARTOD",
              fix="Warnai titik per flag (1 hijau, 3 kuning, 4 merah) dan opsi sembunyikan flag 4.")
    if "table(\"measurements\")" in s and "v_public_measurements" not in s:
        a.add("F08", "medium", "Keamanan", "Dashboard publik membaca tabel mentah, bukan view publik",
              file=f, pattern=r'table\("measurements"\)',
              impact="Butuh akses anon ke tabel mentah (koordinat presisi, data gagal QC).",
              fix="Baca v_public_measurements untuk publik; tabel mentah hanya untuk peneliti yang login.")
    if re.search(r"limit\(500\)", s):
        a.add("F09", "low", "Dashboard", "Hanya 500 baris terakhir dimuat (~5 hari)", file=f, pattern=r"limit\(500\)",
              impact="Unduhan 'dataset lengkap' sebenarnya terpotong.",
              fix="Paginasi (range) atau unduh dari Supabase Storage/ekspor terjadwal.")
    if "wikipedia.org" in s and "Logo" in s:
        a.add("F10", "info", "Dashboard", "Logo ITS di-hotlink dari Wikimedia", file=f, pattern="wikipedia",
              fix="Pastikan izin pemakaian logo institusi; simpan aset lokal.")


# =============================================================================
# G. Python & konsistensi dokumen
# =============================================================================
def check_python(a: Audit):
    pys = a.files("*.py")
    for p in pys:
        r = subprocess.run([sys.executable, "-m", "py_compile", str(p)], capture_output=True, text=True)
        if r.returncode:
            a.add("G01", "high", "Kode", "Gagal compile", file=str(p.relative_to(a.root)), evidence=r.stderr[:150])
    if pys:
        a.ok(f"{len(pys)} berkas Python lolos py_compile")
    try:
        r = subprocess.run([sys.executable, "-m", "pyflakes", *map(str, pys)], capture_output=True, text=True)
        for line in r.stdout.splitlines():
            m = re.match(r"(.+?):(\d+):\d*:? ?(.*)", line)
            if m:
                a.findings.append(Finding("G02", "info", "Kode", "pyflakes: " + m.group(3),
                                          str(Path(m.group(1)).relative_to(a.root)), int(m.group(2))))
    except Exception:
        pass
    dqa = a.read("analysis/dqa_assessment.py")
    if dqa:
        if "expected_count = total_records" in dqa:
            a.add("G03", "medium", "Analisis", "Completeness default = 100% bila expected_count tidak diisi",
                  file="analysis/dqa_assessment.py", pattern="expected_count = total_records",
                  impact="Grade A bisa keluar walau data bolong berhari-hari.",
                  fix="Hitung expected dari rentang waktu deployment / interval (seperti dqa.py di SMMB-docs).")
        if "drop_duplicates" not in dqa and "duplicated" in dqa:
            a.add("G04", "low", "Analisis", "Duplikat dihitung tetapi tidak dibuang sebelum metrik lain",
                  file="analysis/dqa_assessment.py", pattern="duplicated")
        if "Bland" not in dqa and "corrcoef" in dqa:
            a.add("G05", "medium", "Analisis", "Validasi hanya Bias/RMSE/R² — belum Bland–Altman & Deming",
                  file="analysis/dqa_assessment.py", pattern="corrcoef",
                  impact="Proposal (Bab III) menjanjikan Bland–Altman LoA dan regresi Deming; R² tidak mengukur kesesuaian.",
                  fix="Tambah LoA (bias ± 1,96 SD) dan Deming; dqa.py versi SMMB-docs sudah memuat fungsi dasarnya.")
    readme = a.read("README.md")
    if readme and re.search(r"DO|oksigen", readme, re.I) is None and "do_mgl" in a.read("db/schema.sql"):
        a.add("G06", "info", "Dokumen", "Skema punya kolom DO tetapi README/firmware tidak menyebut sensor DO",
              fix="Selaraskan dengan proposal: DO = virtual sensor (RQ4) + DO referensi saat kunjungan.")


# =============================================================================
# Laporan
# =============================================================================
def report(a: Audit, out: Path, as_json: bool) -> Path:
    out.mkdir(parents=True, exist_ok=True)
    f = sorted(a.findings, key=lambda x: (-SEV_ORDER[x.severity], x.id))
    counts = {s: sum(1 for x in f if x.severity == s) for s in SEV_ORDER}
    weights = {"critical": 15, "high": 7, "medium": 3, "low": 1, "info": 0}
    penalty = sum(weights[x.severity] for x in f)
    score = round(100 * 100 / (100 + penalty))
    verdict = ("BELUM SIAP dipakai untuk pengambilan data penelitian" if counts["critical"] else
               "Siap uji lapangan dengan perbaikan" if counts["high"] else "Siap")
    L = ["# Laporan Audit Repositori SMMB", "",
         f"- **Repo:** `{a.root.resolve()}`",
         f"- **Waktu audit:** {datetime.now():%Y-%m-%d %H:%M}",
         f"- **Skor kesehatan:** **{score}/100** (100 × 100 / (100 + penalti); critical 15, high 7, medium 3, low 1)  ·  **Status:** {verdict}",
         "- **Jumlah temuan:** " + " · ".join(f"{SEV_ICON[s]} {s} {counts[s]}" for s in SEV_ORDER), "",
         "## Daftar temuan", "",
         "| # | ID | Tingkat | Area | Temuan | Lokasi |", "|---|---|---|---|---|---|"]
    for i, x in enumerate(f, 1):
        loc = f"`{x.file}{':' + str(x.line) if x.line else ''}`" if x.file else ""
        L.append(f"| {i} | {x.id} | {SEV_ICON[x.severity]} {x.severity} | {x.area} | {x.title} | {loc} |")
    L += ["", "## Rincian dan perbaikan", ""]
    for x in f:
        if x.severity == "info" and not x.fix:
            continue
        L.append(f"### {SEV_ICON[x.severity]} {x.id} — {x.title}")
        if x.file:
            L.append(f"- **Lokasi:** `{x.file}{':' + str(x.line) if x.line else ''}`")
        if x.evidence:
            L.append(f"- **Bukti:** `{x.evidence}`")
        if x.impact:
            L.append(f"- **Dampak:** {x.impact}")
        if x.fix:
            L.append(f"- **Perbaikan:** {x.fix}")
        L.append("")
    L += ["## Yang sudah baik", ""] + [f"- ✅ {p}" for p in a.passed]
    path = out / "AUDIT_REPORT.md"
    path.write_text("\n".join(L), encoding="utf-8")
    if as_json:
        (out / "audit_report.json").write_text(json.dumps(
            {"score": score, "counts": counts, "findings": [asdict(x) for x in f], "passed": a.passed},
            indent=2, ensure_ascii=False))
    return path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("repo", nargs="?", default=".", help="folder repo smart-buoy (default: .)")
    ap.add_argument("--out", default="audit_out", help="folder laporan")
    ap.add_argument("--pg", help='DSN psql untuk uji fungsional, mis. "host=/tmp port=5432 user=postgres"')
    ap.add_argument("--json", action="store_true", help="simpan juga audit_report.json")
    ap.add_argument("--fail-on", choices=list(SEV_ORDER), help="exit 1 bila ada temuan >= tingkat ini")
    args = ap.parse_args()

    a = Audit(Path(args.repo))
    if not (a.root / "db").exists() and not (a.root / "firmware").exists():
        print("Folder ini tidak tampak seperti repo smart-buoy.", file=sys.stderr)
        return 2
    for fn in (check_repo, check_security, check_firmware, check_schema_static,
               check_ingest, check_dashboard, check_python):
        fn(a)
    if args.pg:
        check_schema_live(a, args.pg)
    path = report(a, Path(args.out), args.json)

    c = {s: sum(1 for x in a.findings if x.severity == s) for s in SEV_ORDER}
    print("Audit selesai → " + str(path))
    print("  " + "  ".join(f"{SEV_ICON[s]} {s}: {c[s]}" for s in SEV_ORDER))
    if args.fail_on and any(SEV_ORDER[x.severity] >= SEV_ORDER[args.fail_on] for x in a.findings):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
