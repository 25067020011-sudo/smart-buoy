#!/usr/bin/env python3
"""
audit_repos.py — Clone dan audit repositori open-source pendukung riset SMMB.

Yang dilakukan untuk setiap repo:
  1. git clone --depth 1 (atau git pull bila sudah ada)
  2. Catat commit SHA + tanggal commit terakhir (untuk dikutip di paper: "Code availability")
  3. Deteksi lisensi dari file LICENSE/COPYING (SPDX), sifat copyleft, dan klausul paten
  4. Hitung ukuran: jumlah file, baris kode per bahasa
  5. Cek kelengkapan: README, folder/berkas test, CI (GitHub Actions), CITATION.cff, dokumentasi
  6. Opsional (--smoke): pasang paket Python di virtualenv terpisah dan uji `import`
  7. Beri skor kesiapan (0–100) dan tulis laporan audit_report.md + audit_report.json

Pemakaian:
  python3 audit_repos.py                  # clone + audit statis
  python3 audit_repos.py --smoke          # + uji import paket Python (butuh pip & internet)
  python3 audit_repos.py --out hasil/     # folder keluaran lain
  python3 audit_repos.py --only ioos/ioos_qc TEOS-10/GSW-Python

Hanya memakai pustaka standar Python 3.8+ dan perintah `git`.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import venv
from pathlib import Path

# ---------------------------------------------------------------------------
# Daftar repo: (owner/repo, kegunaan untuk SMMB, nama modul python untuk smoke test)
# ---------------------------------------------------------------------------
REPOS = [
    ("ioos/ioos_qc", "Uji QARTOD (gross range, spike, rate of change, flat line)", "ioos_qc"),
    ("TEOS-10/GSW-Python", "Salinitas PSS-78/TEOS-10 dan DO jenuh (O2sol_SP_pt)", "gsw"),
    ("wesleybowman/UTide", "Analisis harmonik pasang surut M2/S2/K1/O1", "utide"),
    ("OceanographyforEveryone/OpenCTD", "Desain CTD open-hardware & kalibrasi konduktivitas", None),
    ("Atlas-Scientific/Ezo_I2c_lib", "Library ESP32/Arduino sensor EZO (pH, EC, DO, ORP)", None),
    ("DFRobot/DFRobot_PH", "Library & kalibrasi 2 titik sensor pH analog", None),
    ("supabase/supabase", "Backend Postgres, Edge Function, RLS", None),
    ("streamlit/streamlit", "Framework dashboard publik", "streamlit"),
    ("ioos/erddapy", "Ambil data pembanding dari server ERDDAP (NOAA/IOOS)", "erddapy"),
    ("sentinel-hub/sentinelhub-py", "Unduh Sentinel-2 untuk match-up turbiditas", "sentinelhub"),
]

# Repo besar: cukup dianalisis sebagian agar cepat
LARGE_REPOS = {"supabase/supabase", "streamlit/streamlit"}

# ---------------------------------------------------------------------------
# Lisensi
# ---------------------------------------------------------------------------
LICENSE_RULES = [  # (SPDX, regex penanda, copyleft?, hibah paten eksplisit?)
    ("AGPL-3.0", r"GNU AFFERO GENERAL PUBLIC LICENSE", "kuat (jaringan)", True),
    ("GPL-3.0", r"GNU GENERAL PUBLIC LICENSE\s+Version 3", "kuat", True),
    ("GPL-2.0", r"GNU GENERAL PUBLIC LICENSE\s+Version 2", "kuat", False),
    ("LGPL-3.0", r"GNU LESSER GENERAL PUBLIC LICENSE\s+Version 3", "lemah", True),
    ("LGPL-2.1", r"GNU LESSER GENERAL PUBLIC LICENSE\s+Version 2\.1", "lemah", False),
    ("MPL-2.0", r"Mozilla Public License,? (Version|v\.) ?2\.0", "lemah (per berkas)", True),
    ("Apache-2.0", r"Apache License,?\s+Version 2\.0", "tidak", True),
    ("GSW (permisif, mirip BSD)", r"Gibbs SeaWater", "tidak", False),
    ("MIT", r"Permission is hereby granted, free of charge", "tidak", False),
    ("BSD-3-Clause", r"Neither the name of .{0,120} nor the names", "tidak", False),
    ("BSD-2-Clause", r"Redistribution and use in source and binary forms", "tidak", False),
    ("CC-BY-4.0", r"Creative Commons Attribution 4\.0", "tidak (atribusi)", False),
    ("CC-BY-SA-4.0", r"Attribution-ShareAlike 4\.0", "kuat (share-alike)", False),
]
LICENSE_FILES = re.compile(r"^(licen[cs]e|copying|unlicense)(\.[a-z0-9]+)?$", re.I)

LANG_EXT = {
    ".py": "Python", ".c": "C", ".h": "C/C++ header", ".cpp": "C++", ".hpp": "C++",
    ".ino": "Arduino", ".js": "JavaScript", ".jsx": "JavaScript", ".ts": "TypeScript",
    ".tsx": "TypeScript", ".sql": "SQL", ".go": "Go", ".rs": "Rust", ".m": "MATLAB",
    ".f90": "Fortran", ".f": "Fortran", ".sh": "Shell", ".r": "R",
}
SKIP_DIRS = {".git", "node_modules", "dist", "build", ".venv", "venv", "__pycache__", "vendor"}


def run(cmd, cwd=None, timeout=600):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def clone_or_update(full: str, dest: Path) -> tuple[bool, str]:
    url = f"https://github.com/{full}.git"
    if (dest / ".git").exists():
        code, out = run(["git", "pull", "--ff-only", "-q"], cwd=dest)
        return code == 0, out.strip()
    code, out = run(["git", "clone", "-q", "--depth", "1", url, str(dest)], timeout=900)
    return code == 0, out.strip()


def git_meta(dest: Path) -> dict:
    _, sha = run(["git", "rev-parse", "HEAD"], cwd=dest)
    _, date = run(["git", "log", "-1", "--format=%cs"], cwd=dest)
    _, branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=dest)
    _, tag = run(["git", "describe", "--tags", "--abbrev=0"], cwd=dest)
    tag = tag.strip()
    return {
        "commit": sha.strip()[:12],
        "commit_date": date.strip(),
        "branch": branch.strip(),
        "tag": tag if tag and "fatal" not in tag and "No names" not in tag else None,
    }


def detect_license(dest: Path) -> dict:
    files = [f for f in dest.iterdir() if f.is_file() and LICENSE_FILES.match(f.name)]
    if not files:
        return {"file": None, "spdx": "TIDAK DITEMUKAN", "copyleft": "?", "patent_grant": False}
    text = files[0].read_text(errors="ignore")[:20000]
    flat = re.sub(r"\s+", " ", text)
    for spdx, pat, copyleft, patent in LICENSE_RULES:
        if re.search(pat, flat, re.I):
            # BSD-3 punya klausul "Neither the name" -> cek dulu sebelum BSD-2
            return {"file": files[0].name, "spdx": spdx, "copyleft": copyleft,
                    "patent_grant": patent}
    return {"file": files[0].name, "spdx": "tidak dikenali (baca manual)", "copyleft": "?",
            "patent_grant": bool(re.search(r"\bpatent", flat, re.I))}


def code_stats(dest: Path, quick: bool) -> dict:
    langs: dict[str, int] = {}
    n_files = 0
    limit = 4000 if quick else 10**9
    for root, dirs, files in os.walk(dest):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            n_files += 1
            if n_files > limit:
                break
            lang = LANG_EXT.get(Path(name).suffix.lower())
            if not lang:
                continue
            try:
                with open(Path(root) / name, "rb") as fh:
                    langs[lang] = langs.get(lang, 0) + sum(1 for _ in fh)
            except OSError:
                pass
    top = sorted(langs.items(), key=lambda x: -x[1])[:4]
    return {"files": n_files, "loc_by_lang": dict(top), "sampled": quick and n_files > limit}


def completeness(dest: Path) -> dict:
    names = {p.name.lower() for p in dest.iterdir()}
    has = lambda *xs: any(x in names for x in xs)  # noqa: E731
    tests = has("tests", "test", "testing", "__tests__") or any(dest.glob("*/test*")) \
        or any(dest.glob("**/test_*.py"))
    return {
        "readme": any(n.startswith("readme") for n in names),
        "tests": bool(tests),
        "ci": (dest / ".github" / "workflows").exists(),
        "citation": has("citation.cff", "citation.bib", "citation"),
        "docs": has("docs", "doc", "documentation"),
        "changelog": any(n.startswith(("changelog", "changes", "history", "news")) for n in names),
        "examples": has("examples", "example", "notebooks"),
    }


def score(meta: dict, lic: dict, comp: dict) -> int:
    s = 0
    s += 25 if lic["spdx"] not in ("TIDAK DITEMUKAN",) and "tidak dikenali" not in lic["spdx"] else 0
    s += 10 if lic["copyleft"] in ("tidak", "tidak (atribusi)") else 4
    try:
        age = (dt.date.today() - dt.date.fromisoformat(meta["commit_date"])).days
    except ValueError:
        age = 9999
    s += 20 if age <= 180 else 12 if age <= 730 else 4
    s += 10 * comp["tests"] + 8 * comp["ci"] + 7 * comp["readme"]
    s += 6 * comp["docs"] + 6 * comp["citation"] + 4 * comp["examples"] + 4 * comp["changelog"]
    return min(s, 100)


def smoke_test(full: str, module: str | None, dest: Path, work: Path) -> str:
    if not module:
        return "dilewati (bukan paket Python)"
    env_dir = work / "_venv"
    if not env_dir.exists():
        venv.EnvBuilder(with_pip=True).create(env_dir)
    py = env_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    code, out = run([str(py), "-m", "pip", "install", "-q", module.replace("_", "-")
                     if module != "gsw" else "gsw"], timeout=900)
    if code != 0:
        return "GAGAL pip install: " + out.strip().splitlines()[-1][:120]
    code, out = run([str(py), "-c", f"import {module},sys;print(getattr({module},'__version__','?'))"])
    return f"OK (versi {out.strip()})" if code == 0 else "GAGAL import: " + out.strip()[-120:]


def risk_notes(lic: dict, comp: dict, meta: dict) -> list[str]:
    notes = []
    if lic["copyleft"].startswith("kuat"):
        notes.append("Copyleft kuat: modifikasi yang didistribusikan wajib berlisensi sama.")
    elif lic["copyleft"].startswith("lemah"):
        notes.append("Copyleft lemah: perubahan pada library harus dibuka; pemakaian sebagai library aman.")
    if not lic["patent_grant"]:
        notes.append("Tanpa hibah paten eksplisit (lazim untuk MIT/BSD); untuk komersialisasi cek paten.")
    if not comp["tests"]:
        notes.append("Tidak ada test: validasi sendiri sebelum dipakai untuk hasil ilmiah.")
    try:
        if (dt.date.today() - dt.date.fromisoformat(meta["commit_date"])).days > 730:
            notes.append("Tidak aktif > 2 tahun: kunci versi & siapkan fork.")
    except ValueError:
        pass
    return notes


def write_reports(results: list[dict], out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "audit_report.json").write_text(json.dumps(results, indent=2, ensure_ascii=False))
    ok = lambda b: "✓" if b else "—"  # noqa: E731
    L = [f"# Laporan Audit Repositori Pendukung SMMB",
         f"", f"Dibuat: {dt.datetime.now():%Y-%m-%d %H:%M}  ·  Jumlah repo: {len(results)}", "",
         "## Ringkasan", "",
         "| # | Repo | Lisensi | Copyleft | Paten eksplisit | Commit | Tgl commit | Test | CI | Sitasi | Skor |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(results, 1):
        if r.get("error"):
            L.append(f"| {i} | {r['repo']} | GAGAL CLONE | | | | | | | | 0 |")
            continue
        c = r["completeness"]
        L.append(f"| {i} | `{r['repo']}` | {r['license']['spdx']} | {r['license']['copyleft']} | "
                 f"{ok(r['license']['patent_grant'])} | `{r['git']['commit']}` | {r['git']['commit_date']} | "
                 f"{ok(c['tests'])} | {ok(c['ci'])} | {ok(c['citation'])} | **{r['score']}** |")
    L += ["", "## Rincian per repo", ""]
    for r in results:
        L.append(f"### {r['repo']}")
        if r.get("error"):
            L += [f"- Gagal clone: {r['error']}", ""]
            continue
        L += [f"- **Kegunaan untuk SMMB:** {r['purpose']}",
              f"- **Lisensi:** {r['license']['spdx']} (berkas `{r['license']['file']}`)",
              f"- **Versi terkunci:** commit `{r['git']['commit']}` ({r['git']['commit_date']})"
              + (f", tag `{r['git']['tag']}`" if r['git']['tag'] else ""),
              f"- **Ukuran:** {r['stats']['files']} berkas"
              + (" (sampel)" if r['stats']['sampled'] else "")
              + "; baris kode: " + ", ".join(f"{k} {v:,}" for k, v in r['stats']['loc_by_lang'].items()),
              f"- **Uji import:** {r['smoke']}"]
        for n in r["notes"]:
            L.append(f"- ⚠️ {n}")
        L += [f"- **Kutipan (Code availability):** {r['repo']} (commit {r['git']['commit']}, "
              f"{r['git']['commit_date']}), https://github.com/{r['repo']}, lisensi {r['license']['spdx']}.", ""]
    L += ["## Catatan", "",
          "- Skor kesiapan (0–100) = lisensi jelas (25) + sifat permisif (10) + aktivitas (20) + test (10) + CI (8)"
          " + README (7) + docs (6) + CITATION (6) + contoh (4) + changelog (4). Skor bukan penilaian mutu ilmiah.",
          "- Lisensi open source mengatur hak cipta kode. Hanya Apache-2.0, (L)GPL-3.0, dan MPL-2.0 yang memuat hibah paten"
          " eksplisit. Untuk komersialisasi desain buoy, lakukan penelusuran paten (Google Patents / PDKI DJKI).",
          "- Cantumkan commit SHA di atas pada bagian *Code availability* naskah agar hasil dapat direproduksi."]
    (out / "audit_report.md").write_text("\n".join(L), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", default="repos", help="folder tempat clone (default: repos/)")
    ap.add_argument("--out", default="audit_out", help="folder laporan (default: audit_out/)")
    ap.add_argument("--smoke", action="store_true", help="uji pip install + import paket Python")
    ap.add_argument("--only", nargs="*", help="audit sebagian repo saja (owner/repo)")
    a = ap.parse_args()

    if not shutil.which("git"):
        print("ERROR: perintah `git` tidak ditemukan.", file=sys.stderr)
        return 1
    base, out = Path(a.dir), Path(a.out)
    base.mkdir(parents=True, exist_ok=True)
    targets = [r for r in REPOS if not a.only or r[0] in a.only]

    results = []
    for i, (full, purpose, module) in enumerate(targets, 1):
        dest = base / full.replace("/", "__")
        print(f"[{i}/{len(targets)}] {full} ...", end=" ", flush=True)
        ok, msg = clone_or_update(full, dest)
        if not ok:
            print("GAGAL")
            results.append({"repo": full, "purpose": purpose, "error": msg[-200:]})
            continue
        meta, lic, comp = git_meta(dest), detect_license(dest), completeness(dest)
        stats = code_stats(dest, quick=full in LARGE_REPOS)
        smoke = smoke_test(full, module, dest, base) if a.smoke else "tidak dijalankan (pakai --smoke)"
        r = {"repo": full, "purpose": purpose, "git": meta, "license": lic, "completeness": comp,
             "stats": stats, "smoke": smoke, "score": score(meta, lic, comp),
             "notes": risk_notes(lic, comp, meta)}
        results.append(r)
        print(f"{lic['spdx']} · {meta['commit']} · skor {r['score']}")

    write_reports(results, out)
    print(f"\nLaporan: {out/'audit_report.md'} dan {out/'audit_report.json'}")
    return 0 if all(not r.get("error") for r in results) else 2


if __name__ == "__main__":
    sys.exit(main())
