"""Build the unified PRAYUSH predictor — 5 counsellings:
JoSAA R6 + CSAB Special R3 + UPTAC final + GGSIPU R3 + JAC Delhi R5.

Self-contained HTML output (index.html). No external requests at runtime.
"""
import json
import re
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).parent
JOSAA_CSV = ROOT / "josaa_2025_r6_all.csv"
CSAB_CSV = ROOT / "csab_2025_final_all.csv"
UPTAC_CSV = ROOT / "UPTAC" / "uptac_2025_final.csv"
GGSIPU_CSV = ROOT / "ggsipu_2025_final.csv"
JAC_CSV = ROOT / "jac_2025_final.csv"
OUT = ROOT / "index.html"

NIT_GFTI_STATE = {
    "Dr. B R Ambedkar National Institute of Technology, Jalandhar": "Punjab",
    "Indian Institute of Engineering Science and Technology, Shibpur": "West Bengal",
    "Malaviya National Institute of Technology Jaipur": "Rajasthan",
    "Maulana Azad National Institute of Technology Bhopal": "Madhya Pradesh",
    "Motilal Nehru National Institute of Technology Allahabad": "Uttar Pradesh",
    "National Institute of Technology  Agartala": "Tripura",
    "National Institute of Technology Agartala": "Tripura",
    "National Institute of Technology Arunachal Pradesh": "Arunachal Pradesh",
    "National Institute of Technology Calicut": "Kerala",
    "National Institute of Technology Delhi": "Delhi",
    "National Institute of Technology Durgapur": "West Bengal",
    "National Institute of Technology Goa": "Goa",
    "National Institute of Technology Hamirpur": "Himachal Pradesh",
    "National Institute of Technology Karnataka, Surathkal": "Karnataka",
    "National Institute of Technology Meghalaya": "Meghalaya",
    "National Institute of Technology Nagaland": "Nagaland",
    "National Institute of Technology Patna": "Bihar",
    "National Institute of Technology Puducherry": "Puducherry",
    "National Institute of Technology Raipur": "Chhattisgarh",
    "National Institute of Technology Sikkim": "Sikkim",
    "National Institute of Technology, Andhra Pradesh": "Andhra Pradesh",
    "National Institute of Technology, Jamshedpur": "Jharkhand",
    "National Institute of Technology, Kurukshetra": "Haryana",
    "National Institute of Technology, Manipur": "Manipur",
    "National Institute of Technology, Mizoram": "Mizoram",
    "National Institute of Technology, Rourkela": "Odisha",
    "National Institute of Technology, Silchar": "Assam",
    "National Institute of Technology, Srinagar": "Jammu & Kashmir",
    "National Institute of Technology, Tiruchirappalli": "Tamil Nadu",
    "National Institute of Technology, Uttarakhand": "Uttarakhand",
    "National Institute of Technology, Warangal": "Telangana",
    "Sardar Vallabhbhai National Institute of Technology, Surat": "Gujarat",
    "Visvesvaraya National Institute of Technology, Nagpur": "Maharashtra",
    "Assam University, Silchar": "Assam",
    "Birla Institute of Technology, Deoghar Off-Campus": "Jharkhand",
    "Birla Institute of Technology, Mesra,  Ranchi": "Jharkhand",
    "Birla Institute of Technology, Patna Off-Campus": "Bihar",
    "Ghani Khan Choudhary Institute of Engineering and Technology, Malda, West Bengal": "West Bengal",
    "Institute of Chemical Technology, Mumbai: Indian Oil Odisha Campus, Bhubaneswar": "Odisha",
    "Islamic University of Science and Technology Kashmir": "Jammu & Kashmir",
    "Puducherry Technological University, Puducherry": "Puducherry",
    "Punjab Engineering College, Chandigarh": "Chandigarh",
}

CSAB_QUOTA_MAP = {
    "All India": "AI",
    "Home State": "HS",
    "Other State": "OS",
    "Home State for Goa": "GO",
    "Jammu & Kashmir (UT)": "JK",
    "DASA-CIWG": "DASA-CIWG",
    "DASA-Non CIWG": "DASA-Non CIWG",
}

def load_jc(csv_path: Path, round_label: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df = df[["Institute Type", "Institute", "Academic Program Name",
             "Quota", "Seat Type", "Gender",
             "Opening Rank (int)", "Closing Rank (int)"]].copy()
    df.columns = ["type", "inst", "prog", "quota", "seat", "gender", "open", "close"]
    df = df.dropna(subset=["open", "close"])
    df["open"] = df["open"].astype(int)
    df["close"] = df["close"].astype(int)
    df["round"] = round_label
    df["note"] = ""
    return df


def load_uptac() -> pd.DataFrame:
    df = pd.read_csv(UPTAC_CSV)
    df = df.rename(columns={
        "Institute": "inst", "Program": "prog", "Quota": "quota",
        "Seat": "seat", "Gender": "gender", "Note": "note",
        "Opening Rank (int)": "open", "Closing Rank (int)": "close",
    })
    df = df.dropna(subset=["open", "close"])
    df["open"] = df["open"].astype(int)
    df["close"] = df["close"].astype(int)
    df["round"] = "UPTAC"
    df["type"] = "UPTAC"
    df["note"] = df["note"].fillna("")
    return df[["round", "type", "inst", "prog", "quota", "seat", "gender", "open", "close", "note"]]


def load_ggsipu() -> pd.DataFrame:
    df = pd.read_csv(GGSIPU_CSV)
    df = df.rename(columns={
        "Institute": "inst", "Program": "prog", "Quota": "quota",
        "Seat": "seat", "Gender": "gender", "Note": "note",
        "Opening Rank (int)": "open", "Closing Rank (int)": "close",
    })
    df = df.dropna(subset=["open", "close"])
    df["open"] = df["open"].astype(int)
    df["close"] = df["close"].astype(int)
    df["round"] = "GGSIPU"
    df["type"] = "GGSIPU"
    df["note"] = df["note"].fillna("")
    return df[["round", "type", "inst", "prog", "quota", "seat", "gender", "open", "close", "note"]]


def load_jac() -> pd.DataFrame:
    df = pd.read_csv(JAC_CSV)
    df = df.rename(columns={
        "Institute": "inst", "Program": "prog", "Quota": "quota",
        "Seat": "seat", "Gender": "gender", "Note": "note",
        "Opening Rank (int)": "open", "Closing Rank (int)": "close",
    })
    df = df.dropna(subset=["open", "close"])
    df["open"] = df["open"].astype(int)
    df["close"] = df["close"].astype(int)
    df["round"] = "JAC"
    df["type"] = "JAC"
    df["note"] = df["note"].fillna("")
    return df[["round", "type", "inst", "prog", "quota", "seat", "gender", "open", "close", "note"]]


josaa = load_jc(JOSAA_CSV, "JoSAA")
csab = load_jc(CSAB_CSV, "CSAB")
csab["quota"] = csab["quota"].map(lambda q: CSAB_QUOTA_MAP.get(q, q))
uptac = load_uptac()
ggsipu = load_ggsipu()
jac = load_jac()

merged = pd.concat([josaa, csab, uptac, ggsipu, jac], ignore_index=True)
print(f"JoSAA: {len(josaa):,}  CSAB: {len(csab):,}  UPTAC: {len(uptac):,}  GGSIPU: {len(ggsipu):,}  JAC: {len(jac):,}  TOTAL pre-filter: {len(merged):,}")

# Drop architecture and planning courses entirely (Paper-2 / non-B.Tech).
#   - JoSAA / CSAB: "Architecture  (5 Years, Bachelor of Architecture)"
#   - JoSAA / CSAB: "Planning (4 Years, Bachelor of Planning)"
#   - GGSIPU:       "B.Tech. (Architecture & interior Decoration)"
arch_re = re.compile(r"architecture|planning", re.I)
arch_mask = merged["prog"].astype(str).str.contains(arch_re, na=False)
dropped_arch = int(arch_mask.sum())
merged = merged[~arch_mask].reset_index(drop=True)
print(f"Dropped {dropped_arch} architecture/planning rows · TOTAL: {len(merged):,}")

# UPTAC = UP; GGSIPU & JAC = Delhi for HS quota gating
INST_STATE = dict(NIT_GFTI_STATE)
for inst in uptac["inst"].unique():
    INST_STATE[inst] = "Uttar Pradesh"
for inst in ggsipu["inst"].unique():
    INST_STATE[inst] = "Delhi"
for inst in jac["inst"].unique():
    INST_STATE[inst] = "Delhi"

STATES = sorted(set(INST_STATE.values()) | {
    "Andaman & Nicobar Islands", "Bihar", "Dadra & Nagar Haveli and Daman & Diu",
    "Lakshadweep", "Ladakh"
})

cols = ["round", "type", "inst", "prog", "quota", "seat", "gender", "open", "close", "note"]
data_arr = [[r[c] for c in cols] for r in merged.to_dict(orient="records")]

# ===================== HTML =====================
HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PRAYUSH · Unified JEE Counselling Predictor — JoSAA + CSAB + UPTAC + GGSIPU + JAC Delhi</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #ffffff;
    --surface: #ffffff;
    --surface-2: #f9fafb;
    --surface-3: #f3f4f6;
    --line: #e5e7eb;
    --line-strong: #d1d5db;
    --ink: #0a0a0a;
    --ink-2: #111827;
    --ink-dim: #4b5563;
    --ink-faint: #9ca3af;
    --accent: #2563eb;
    --accent-hover: #1d4ed8;
    --accent-soft: #eff6ff;
    --accent-soft-2: #dbeafe;
    --success: #059669;
    --success-soft: #d1fae5;
    --warn-soft: #fef3c7;
    --warn-ink: #78350f;
    --danger: #dc2626;

    --josaa: #0891b2;
    --csab:  #db2777;
    --uptac: #d97706;
    --ggsipu:#65a30d;
    --jac:   #4f46e5;

    --shadow-sm: 0 1px 2px rgba(15,23,42,0.04);
    --shadow:    0 1px 3px rgba(15,23,42,0.06), 0 1px 2px rgba(15,23,42,0.04);
    --shadow-md: 0 4px 6px -1px rgba(15,23,42,0.06), 0 2px 4px -2px rgba(15,23,42,0.04);
    --shadow-lg: 0 10px 25px -3px rgba(15,23,42,0.08), 0 4px 6px -2px rgba(15,23,42,0.04);

    --radius: 10px;
    --radius-lg: 14px;
  }
  * { box-sizing: border-box; }
  html, body { height: 100%; margin: 0; }
  body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: var(--bg);
    color: var(--ink-2);
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    font-size: 15px;
    line-height: 1.5;
    overflow-x: hidden;
  }

  /* Subtle grid background */
  .bg-grid {
    position: fixed; inset: 0; z-index: -1; pointer-events: none;
    background-image:
      linear-gradient(rgba(15,23,42,0.04) 1px, transparent 1px),
      linear-gradient(90deg, rgba(15,23,42,0.04) 1px, transparent 1px);
    background-size: 44px 44px;
    -webkit-mask-image: radial-gradient(ellipse 70% 55% at 50% 30%, #000 35%, transparent 85%);
            mask-image: radial-gradient(ellipse 70% 55% at 50% 30%, #000 35%, transparent 85%);
  }

  /* === Top brand bar === */
  .topbar {
    border-bottom: 1px solid var(--line);
    background: #fff;
    position: relative; z-index: 5;
  }
  .topbar-inner {
    max-width: 1240px; margin: 0 auto;
    padding: 14px 32px;
    display: flex; align-items: center; gap: 18px;
  }
  .brand-mark {
    display: flex; align-items: center; gap: 10px;
    text-decoration: none;
  }
  .brand-mark .logo {
    width: 34px; height: 34px; flex-shrink: 0;
    border-radius: 8px;
    background: var(--accent);
    display: flex; align-items: center; justify-content: center;
    color: #fff; font-weight: 800; font-size: 16px;
    letter-spacing: 0;
  }
  .brand-mark .wordmark {
    display: flex; flex-direction: column; line-height: 1.1;
  }
  .brand-mark .wm-top { font-size: 15px; font-weight: 700; color: var(--ink-2); letter-spacing: -0.005em; }
  .brand-mark .wm-sub { font-size: 11px; font-weight: 500; color: var(--ink-dim); }
  .topbar-spacer { flex: 1; }
  .topbar-link {
    font-size: 13px; font-weight: 500; color: var(--ink-dim);
    text-decoration: none;
  }
  .topbar-link:hover { color: var(--ink-2); }

  /* === Announcement banner === */
  .announce {
    background: var(--surface-2);
    border-bottom: 1px solid var(--line);
    padding: 12px 32px;
  }
  .announce-inner {
    max-width: 1240px; margin: 0 auto;
    display: flex; align-items: center; justify-content: center; gap: 14px;
    font-size: 14px; color: var(--ink-2);
    flex-wrap: wrap;
  }
  .avatar-row { display: inline-flex; flex-shrink: 0; }
  .avatar-row .av {
    width: 28px; height: 28px; border-radius: 50%;
    border: 2px solid #fff;
    margin-left: -8px;
    background: linear-gradient(135deg, #fbbf24, #f59e0b);
    box-shadow: var(--shadow-sm);
  }
  .avatar-row .av:first-child { margin-left: 0; background: linear-gradient(135deg, #60a5fa, #2563eb); }
  .avatar-row .av:nth-child(2) { background: linear-gradient(135deg, #fb7185, #e11d48); }
  .avatar-row .av:nth-child(3) { background: linear-gradient(135deg, #34d399, #059669); }
  .announce-num { color: var(--accent); font-weight: 700; }

  /* === Shell / hero === */
  .shell { max-width: 1240px; margin: 0 auto; padding: 60px 32px 80px; }

  .hero {
    display: grid;
    grid-template-columns: minmax(0, 1.15fr) minmax(380px, 1fr);
    gap: 60px;
    align-items: start;
  }

  .badge {
    display: inline-flex; align-items: center; gap: 7px;
    padding: 6px 12px; border-radius: 999px;
    background: var(--success-soft); color: #047857;
    font-size: 13px; font-weight: 500;
    margin-bottom: 24px;
  }
  .badge svg { width: 14px; height: 14px; }

  .hero h1 {
    font-size: clamp(38px, 4.4vw, 56px);
    line-height: 1.05;
    letter-spacing: -0.025em;
    font-weight: 700;
    margin: 0 0 20px;
    color: var(--ink);
  }
  .hero h1 .blue { color: var(--accent); display: block; }
  .hero p {
    font-size: 17px; line-height: 1.55;
    color: var(--ink-dim);
    max-width: 540px; margin: 0 0 28px;
  }
  .hero p b { color: var(--ink-2); font-weight: 600; }

  .collab {
    display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
    margin-bottom: 32px;
    padding: 16px 0;
    border-top: 1px solid var(--line);
    border-bottom: 1px solid var(--line);
  }
  .collab .label { font-size: 13px; color: var(--ink-dim); margin-right: 4px; }
  .src-pill {
    display: inline-flex; align-items: center; gap: 7px;
    padding: 6px 12px; border-radius: 999px;
    background: #fff; border: 1px solid var(--line);
    font-size: 12px; font-weight: 600; color: var(--ink-2);
    box-shadow: var(--shadow-sm);
  }
  .src-pill .dot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
  .src-pill.j .dot { background: var(--josaa); }
  .src-pill.c .dot { background: var(--csab); }
  .src-pill.u .dot { background: var(--uptac); }
  .src-pill.g .dot { background: var(--ggsipu); }
  .src-pill.a .dot { background: var(--jac); }

  .features {
    display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px;
  }
  .feature {
    display: flex; align-items: center; gap: 12px;
    padding: 14px 16px;
    background: #fff;
    border: 1px solid var(--line);
    border-radius: var(--radius);
    box-shadow: var(--shadow-sm);
  }
  .feature-icon {
    width: 36px; height: 36px; border-radius: 50%;
    background: var(--accent-soft); color: var(--accent);
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
  }
  .feature-icon svg { width: 18px; height: 18px; }
  .feature .v { font-weight: 700; font-size: 15px; line-height: 1.2; color: var(--ink-2); }
  .feature .l { font-size: 12px; color: var(--ink-dim); margin-top: 2px; }

  /* === Form card === */
  .form-card {
    background: #fff;
    border: 1px solid var(--line);
    border-radius: 16px;
    padding: 28px;
    box-shadow: var(--shadow-md);
  }
  .field { margin-bottom: 16px; }
  .field-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
  .field-grid .field { margin-bottom: 16px; }
  .field label {
    display: block;
    font-size: 13px; font-weight: 500; color: var(--ink-2);
    margin-bottom: 6px;
  }
  .field label .req { color: var(--danger); }
  .field label .opt { color: var(--ink-faint); font-weight: 400; font-size: 12px; }

  input, select {
    width: 100%; padding: 11px 13px;
    background: #fff; color: var(--ink-2);
    border: 1px solid var(--line); border-radius: 8px;
    font-size: 14px; font-family: inherit; font-weight: 500;
    transition: border-color 0.15s, box-shadow 0.15s;
    -webkit-appearance: none; appearance: none;
  }
  input::placeholder { color: var(--ink-faint); font-weight: 400; }
  input:focus, select:focus {
    outline: none;
    border-color: var(--accent);
    box-shadow: 0 0 0 3px rgba(37,99,235,0.12);
  }
  select {
    background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='14' height='14' viewBox='0 0 24 24' fill='none' stroke='%236b7280' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'><polyline points='6 9 12 15 18 9'/></svg>");
    background-repeat: no-repeat;
    background-position: right 12px center;
    padding-right: 36px;
  }

  /* === Phone + OTP === */
  .phone-row { display: flex; gap: 8px; }
  .phone-row .cc-prefix {
    display: inline-flex; align-items: center;
    padding: 0 12px; height: 42px;
    background: var(--surface-2); border: 1px solid var(--line);
    border-radius: 8px;
    color: var(--ink-2); font-size: 14px; font-weight: 600;
    flex-shrink: 0;
  }
  .phone-row input { flex: 1; min-width: 0; }

  .or-divider {
    display: flex; align-items: center; gap: 12px;
    margin: 6px 0 12px;
    color: var(--ink-faint); font-size: 12px; font-weight: 500;
    letter-spacing: 0.04em;
  }
  .or-divider::before, .or-divider::after {
    content: ''; flex: 1; height: 1px; background: var(--line);
  }

  .tip {
    display: flex; align-items: center; gap: 8px;
    padding: 10px 12px; border-radius: 8px;
    background: var(--warn-soft); color: var(--warn-ink);
    font-size: 13px; font-weight: 500;
    margin-bottom: 16px;
    border: 1px solid #fde68a;
  }
  .tip svg { width: 14px; height: 14px; flex-shrink: 0; }

  .radio-group {
    display: grid; grid-template-columns: 1fr 1fr; gap: 10px;
  }
  .radio-option {
    display: flex; align-items: center; gap: 10px;
    padding: 11px 14px;
    background: #fff;
    border: 1px solid var(--line); border-radius: 8px;
    cursor: pointer; user-select: none;
    font-size: 14px; font-weight: 500;
    transition: border-color 0.15s, background 0.15s;
  }
  .radio-option:hover { border-color: var(--line-strong); }
  .radio-option.selected { border-color: var(--accent); background: var(--accent-soft); }
  .radio-option .dot {
    width: 16px; height: 16px; border-radius: 50%;
    border: 1.5px solid var(--ink-faint);
    position: relative; flex-shrink: 0;
    transition: border-color 0.15s;
  }
  .radio-option.selected .dot { border-color: var(--accent); }
  .radio-option.selected .dot::after {
    content: ''; position: absolute; inset: 3px;
    border-radius: 50%; background: var(--accent);
  }

  /* Counsellings to include — compact pills inside the form */
  .counsel-row { display: flex; gap: 6px; flex-wrap: wrap; }
  .round-card {
    padding: 7px 12px; border-radius: 8px;
    background: #fff; border: 1px solid var(--line);
    font-size: 12px; font-weight: 600; color: var(--ink-dim);
    cursor: pointer; user-select: none;
    display: inline-flex; align-items: center; gap: 6px;
    transition: border-color 0.15s, background 0.15s, color 0.15s;
  }
  .round-card:hover { border-color: var(--line-strong); color: var(--ink-2); }
  .round-card .head { display: inline; }
  .round-card .name { display: inline; }
  .round-card .name .check, .round-card .desc, .round-card .count { display: none; }
  .round-card.on { border-color: var(--accent); background: var(--accent-soft); color: var(--accent); }

  /* CTA button */
  button.cta {
    width: 100%; padding: 14px;
    background: #0a0a0a; color: #fff;
    border: none; border-radius: 8px;
    font-size: 15px; font-weight: 600; font-family: inherit;
    cursor: pointer;
    transition: background 0.15s, transform 0.1s;
    margin-top: 4px;
  }
  button.cta:hover { background: #1f2937; }
  button.cta:active { transform: translateY(1px); }

  .trust-row {
    margin-top: 14px;
    display: flex; align-items: center; justify-content: center;
    gap: 7px;
    font-size: 13px; font-weight: 500; color: var(--success);
  }
  .trust-row svg { width: 14px; height: 14px; }

  /* === Generic buttons (filter reset, exports) === */
  button {
    padding: 9px 16px; font-size: 13px; font-weight: 600;
    border: 1px solid var(--line); border-radius: 8px;
    cursor: pointer; font-family: inherit;
    background: #fff; color: var(--ink-2);
    transition: background 0.15s, border-color 0.15s;
  }
  button:hover { background: var(--surface-2); border-color: var(--line-strong); }
  button.ghost { background: transparent; border-color: transparent; color: var(--ink-dim); }
  button.ghost:hover { color: var(--ink-2); background: var(--surface-2); }

  /* === Results panel === */
  .panel {
    background: #fff;
    border: 1px solid var(--line);
    border-radius: var(--radius-lg);
    padding: 22px;
    box-shadow: var(--shadow-sm);
  }
  .panel + .panel { margin-top: 16px; }

  .section-title {
    font-size: 14px; font-weight: 600; color: var(--ink-2);
    margin: 0 0 14px;
    display: flex; align-items: center; gap: 10px;
  }

  .filter-bar { display: flex; gap: 14px; flex-wrap: wrap; align-items: flex-end; }
  .filter-group { display: flex; flex-direction: column; gap: 6px; min-width: 150px; }
  .filter-group label {
    font-size: 12px; font-weight: 500; color: var(--ink-dim);
    margin: 0;
  }

  .chip-row { display: flex; gap: 6px; flex-wrap: wrap; }
  .chip {
    padding: 6px 12px; border-radius: 999px; font-size: 12px; font-weight: 600;
    background: #fff; border: 1px solid var(--line);
    cursor: pointer; user-select: none;
    color: var(--ink-dim);
    transition: border-color 0.15s, background 0.15s, color 0.15s;
  }
  .chip:hover { border-color: var(--line-strong); color: var(--ink-2); }
  .chip.on { background: var(--accent-soft); border-color: var(--accent); color: var(--accent); }
  .chip[data-src="JoSAA"].on  { background: #ecfeff; border-color: var(--josaa);  color: #0e7490; }
  .chip[data-src="CSAB"].on   { background: #fdf2f8; border-color: var(--csab);   color: #be185d; }
  .chip[data-src="UPTAC"].on  { background: #fffbeb; border-color: var(--uptac);  color: #b45309; }
  .chip[data-src="GGSIPU"].on { background: #f7fee7; border-color: var(--ggsipu); color: #4d7c0f; }
  .chip[data-src="JAC"].on    { background: #eef2ff; border-color: var(--jac);    color: #4338ca; }

  /* === Table === */
  .table-wrap {
    max-height: 65vh; overflow: auto;
    border-radius: 12px; border: 1px solid var(--line);
    background: #fff;
  }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  thead th {
    position: sticky; top: 0; z-index: 2;
    background: var(--surface-2);
    text-align: left; padding: 11px 14px;
    font-size: 12px; font-weight: 600; color: var(--ink-dim);
    border-bottom: 1px solid var(--line);
    cursor: pointer; user-select: none; white-space: nowrap;
  }
  thead th:hover { color: var(--ink-2); }
  thead th.sortable::after { content: ' ⇅'; opacity: 0.4; font-size: 10px; }
  thead th.sort-asc::after { content: ' ↑'; opacity: 1; color: var(--accent); }
  thead th.sort-desc::after { content: ' ↓'; opacity: 1; color: var(--accent); }
  tbody td {
    padding: 11px 14px; border-bottom: 1px solid var(--surface-3);
    color: var(--ink-2);
  }
  tbody tr:last-child td { border-bottom: none; }
  tbody tr:hover td { background: var(--surface-2); }
  td.numcell { text-align: right; font-family: 'JetBrains Mono', monospace; font-weight: 600; color: var(--ink); }

  .pill {
    display: inline-block; padding: 3px 9px; border-radius: 999px;
    font-size: 11px; font-weight: 600; line-height: 1.4;
  }
  .pill-NIT    { background: #ecfdf5; color: #047857; }
  .pill-IIIT   { background: #f5f3ff; color: #6d28d9; }
  .pill-GFTI   { background: #fffbeb; color: #b45309; }
  .pill-UPTAC  { background: #fef3c7; color: #92400e; }
  .pill-GGSIPU { background: #ecfccb; color: #4d7c0f; }
  .pill-JAC    { background: #eef2ff; color: #4338ca; }
  .pill-JoSAA    { background: #ecfeff; color: #0e7490; border: 1px solid #a5f3fc; }
  .pill-CSAB     { background: #fdf2f8; color: #be185d; border: 1px solid #fbcfe8; }
  .pill-UPTAC-r  { background: #fffbeb; color: #b45309; border: 1px solid #fde68a; }
  .pill-GGSIPU-r { background: #f7fee7; color: #4d7c0f; border: 1px solid #d9f99d; }
  .pill-JAC-r    { background: #eef2ff; color: #4338ca; border: 1px solid #c7d2fe; }
  .pill-quota    { background: var(--surface-3); color: var(--ink-dim); }
  .pill-note     { background: #f5f3ff; color: #6d28d9; margin-left: 4px; }

  /* === Toolbar above table === */
  .toolbar { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; margin-bottom: 14px; }
  .toolbar .grow { flex: 1; }
  .toolbar strong { font-size: 14px; font-weight: 600; color: var(--ink-2); }
  .vis-pill {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 5px 11px; border-radius: 999px;
    background: var(--accent-soft); color: var(--accent);
    border: 1px solid var(--accent-soft-2);
    font-family: 'JetBrains Mono', monospace; font-size: 12px; font-weight: 700;
  }

  .footer-note {
    font-size: 12px; color: var(--ink-dim); margin-top: 18px; line-height: 1.7;
    border-top: 1px solid var(--line); padding-top: 14px;
  }
  .footer-note b { color: var(--ink-2); font-weight: 600; }
  .footer-note a { color: var(--accent); text-decoration: none; }
  .footer-note a:hover { text-decoration: underline; }

  /* === Empty hero === */
  .empty-hero {
    background: var(--surface-2);
    border: 1px dashed var(--line-strong);
    border-radius: var(--radius-lg);
    padding: 56px 30px; text-align: center;
  }
  .empty-hero .icon {
    width: 56px; height: 56px; border-radius: 50%;
    background: var(--accent-soft); color: var(--accent);
    display: flex; align-items: center; justify-content: center;
    margin: 0 auto 16px;
  }
  .empty-hero .icon svg { width: 28px; height: 28px; }
  .empty-hero h2 { font-weight: 700; font-size: 22px; margin: 0 0 8px; letter-spacing: -0.015em; color: var(--ink); }
  .empty-hero p { color: var(--ink-dim); font-size: 14px; max-width: 520px; margin: 0 auto; line-height: 1.6; }

  .hidden { display: none !important; }

  /* Scrollbars (light) */
  ::-webkit-scrollbar { width: 10px; height: 10px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: var(--surface-3); border-radius: 10px; border: 2px solid #fff; }
  ::-webkit-scrollbar-thumb:hover { background: var(--line-strong); }

  @media (max-width: 980px) {
    .hero { grid-template-columns: 1fr; gap: 40px; }
    .features { grid-template-columns: 1fr; }
    .shell { padding: 40px 24px 60px; }
  }
  @media (max-width: 640px) {
    .topbar-inner { padding: 12px 16px; }
    .announce { padding: 10px 16px; }
    .announce-inner { font-size: 13px; }
    .shell { padding: 32px 16px 56px; }
    .hero h1 { font-size: 36px; }
    .hero p { font-size: 15px; }
    .form-card { padding: 22px; }
    .filter-bar { gap: 12px; }
  }
</style>
</head>
<body>
<div class="bg-grid"></div>

<header class="topbar">
  <div class="topbar-inner">
    <a class="brand-mark" href="#">
      <div class="logo">P</div>
      <div class="wordmark">
        <span class="wm-top">PRAYUSH</span>
        <span class="wm-sub">JEE Counselling Predictor</span>
      </div>
    </a>
    <div class="topbar-spacer"></div>
    <a class="topbar-link" href="https://josaa.admissions.nic.in" target="_blank" rel="noopener">Sources</a>
  </div>
</header>

<div class="announce">
  <div class="announce-inner">
    <span class="avatar-row"><span class="av"></span><span class="av"></span><span class="av"></span></span>
    <span><span class="announce-num" id="announceCount">0</span> cutoffs unified across 5 official 2025 counsellings</span>
  </div>
</div>

<main class="shell">
  <section class="hero">
    <div class="hero-left">
      <div class="badge">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M9 12l2 2 4-4"/><circle cx="12" cy="12" r="10"/></svg>
        100% Free · No Sign-up · Runs Offline
      </div>
      <h1>
        <span class="blue">JEE Main &amp; Counselling</span>
        College Predictor 2025
      </h1>
      <p>Get accurate college predictions across every major JEE counselling — built from official 2025 cutoff data spanning <b>NITs, IIITs, GFTIs, UPTAC, GGSIPU,</b> and <b>JAC Delhi</b>. One rank. One ranked choice list.</p>

      <div class="collab">
        <span class="label">Built from data:</span>
        <span class="src-pill j"><span class="dot"></span>JoSAA · R6</span>
        <span class="src-pill c"><span class="dot"></span>CSAB · Special</span>
        <span class="src-pill u"><span class="dot"></span>UPTAC · Final</span>
        <span class="src-pill g"><span class="dot"></span>GGSIPU · R3</span>
        <span class="src-pill a"><span class="dot"></span>JAC Delhi · R5</span>
      </div>

      <div class="features">
        <div class="feature">
          <div class="feature-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
          </div>
          <div>
            <div class="v"><span id="totalCount">0</span></div>
            <div class="l">Cutoff Records</div>
          </div>
        </div>
        <div class="feature">
          <div class="feature-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/></svg>
          </div>
          <div>
            <div class="v">5 Counsellings</div>
            <div class="l">Unified Search</div>
          </div>
        </div>
        <div class="feature">
          <div class="feature-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0110 0v4"/></svg>
          </div>
          <div>
            <div class="v">Private &amp; Offline</div>
            <div class="l">No Tracking</div>
          </div>
        </div>
      </div>
    </div>

    <aside class="hero-right">
      <form class="form-card" onsubmit="event.preventDefault(); runPredict();">
        <div class="field">
          <label>Your Name <span class="req">*</span></label>
          <input id="name" placeholder="e.g. Ankit Sharma" required>
        </div>

        <div class="field">
          <label>Phone <span class="req">*</span></label>
          <div class="phone-row">
            <span class="cc-prefix">+91</span>
            <input id="phone" type="tel" placeholder="10-digit number" inputmode="numeric" required maxlength="10" autocomplete="tel-national">
          </div>
        </div>

        <div class="field">
          <label>Email <span class="req">*</span></label>
          <input id="email" type="email" placeholder="e.g. you@example.com" required>
        </div>

        <div class="field">
          <label>JEE Main 2025 Rank <span class="req">*</span></label>
          <input id="crl" type="number" placeholder="Your CRL (e.g. 50000)" min="1">
        </div>

        <div class="or-divider">OR</div>

        <div class="field">
          <label>Category Rank <span class="opt">(JoSAA only)</span></label>
          <input id="rank" type="number" placeholder="e.g. 12000" min="1">
        </div>

        <div class="tip">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
          <span>Enter category rank for sharper JoSAA predictions.</span>
        </div>

        <div class="field">
          <label>Category <span class="req">*</span></label>
          <select id="seatType">
            <option>OPEN</option><option>EWS</option><option>OBC-NCL</option>
            <option>SC</option><option>ST</option>
            <option>OPEN (PwD)</option><option>EWS (PwD)</option>
            <option>OBC-NCL (PwD)</option><option>SC (PwD)</option><option>ST (PwD)</option>
          </select>
        </div>

        <div class="field">
          <label>Seat Pool <span class="req">*</span></label>
          <div class="radio-group" id="genderGroup">
            <div class="radio-option selected" data-value="M">
              <span class="dot"></span><span>Gender Neutral</span>
            </div>
            <div class="radio-option" data-value="F">
              <span class="dot"></span><span>Female</span>
            </div>
          </div>
          <input type="hidden" id="gender" value="M">
        </div>

        <div class="field">
          <label>Home State <span class="req">*</span></label>
          <select id="homeState"></select>
        </div>

        <div class="field">
          <label>Budget for Full Course <span class="req">*</span></label>
          <select id="budget">
            <option value="">No budget constraints</option>
            <option value="Under 5 Lakhs">Under 5 Lakhs</option>
            <option value="5-7 Lakhs">5-7 Lakhs</option>
            <option value="7-10 Lakhs">7-10 Lakhs</option>
            <option value="10-14 Lakhs">10-14 Lakhs</option>
            <option value="14-18 Lakhs">14-18 Lakhs</option>
            <option value="18-22 Lakhs">18-22 Lakhs</option>
            <option value="22-26 Lakhs">22-26 Lakhs</option>
          </select>
        </div>

        <div class="field" style="margin-bottom:20px;">
          <label>Counsellings to include</label>
          <div class="counsel-row" id="roundToggle">
            <div class="round-card on" data-round="JoSAA"><div class="head"><div class="name">JoSAA<span class="check"></span></div></div><div class="desc"></div><div class="count" id="cJoSAA"></div></div>
            <div class="round-card on" data-round="CSAB"><div class="head"><div class="name">CSAB<span class="check"></span></div></div><div class="desc"></div><div class="count" id="cCSAB"></div></div>
            <div class="round-card on" data-round="UPTAC"><div class="head"><div class="name">UPTAC<span class="check"></span></div></div><div class="desc"></div><div class="count" id="cUPTAC"></div></div>
            <div class="round-card on" data-round="GGSIPU"><div class="head"><div class="name">GGSIPU<span class="check"></span></div></div><div class="desc"></div><div class="count" id="cGGSIPU"></div></div>
            <div class="round-card on" data-round="JAC"><div class="head"><div class="name">JAC Delhi<span class="check"></span></div></div><div class="desc"></div><div class="count" id="cJAC"></div></div>
          </div>
        </div>

        <button type="submit" class="cta">Predict My Colleges</button>

        <div class="trust-row">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M9 12l2 2 4-4"/><circle cx="12" cy="12" r="10"/></svg>
          No Hidden Charges, 100% Free
        </div>
      </form>
    </aside>
  </section>

  <!-- Hidden counters that JS animates (no longer rendered visibly) -->
  <span style="display:none;" aria-hidden="true">
    <span id="josaaCountTop">0</span><span id="csabCountTop">0</span>
    <span id="uptacCountTop">0</span><span id="ggsipuCountTop">0</span>
    <span id="jacCountTop">0</span>
  </span>

  <div id="resultsSection" class="hidden" style="margin-top:32px;">
    <div class="panel">
      <div class="section-title">Refine Results</div>
      <div class="filter-bar">
        <div class="filter-group">
          <label>Institute Type</label>
          <div class="chip-row" id="typeChips">
            <div class="chip on" data-type="NIT">NIT</div>
            <div class="chip on" data-type="IIIT">IIIT</div>
            <div class="chip on" data-type="GFTI">GFTI</div>
            <div class="chip on" data-type="UPTAC">UPTAC</div>
            <div class="chip on" data-type="GGSIPU">GGSIPU</div>
            <div class="chip on" data-type="JAC">JAC</div>
          </div>
        </div>
        <div class="filter-group">
          <label>Source</label>
          <div class="chip-row" id="srcChips">
            <div class="chip on" data-src="JoSAA">JoSAA</div>
            <div class="chip on" data-src="CSAB">CSAB</div>
            <div class="chip on" data-src="UPTAC">UPTAC</div>
            <div class="chip on" data-src="GGSIPU">GGSIPU</div>
            <div class="chip on" data-src="JAC">JAC</div>
          </div>
        </div>
        <div class="filter-group">
          <label>Quota</label>
          <select id="quotaFilter" multiple size="1" style="min-width:160px"></select>
        </div>
        <div class="filter-group">
          <label>Institute</label>
          <select id="instFilter" multiple size="1" style="min-width:220px"></select>
        </div>
        <div class="filter-group">
          <label>Program contains</label>
          <input id="search" placeholder="e.g. Computer Science…">
        </div>
        <div class="filter-group" style="align-self:end;">
          <button class="ghost" onclick="resetFilters()">Reset filters</button>
        </div>
      </div>
    </div>

    <div class="panel">
      <div class="toolbar">
        <strong>Your preference list</strong>
        <span class="vis-pill" id="visCount">0 options</span>
        <div class="grow"></div>
        <button onclick="downloadCSV()">Download CSV</button>
        <button onclick="downloadXLSX()">Download Excel</button>
        <button class="ghost" onclick="downloadPDF()">Print / PDF</button>
        <button class="ghost" onclick="resetAll()">New search</button>
      </div>
      <div class="table-wrap">
        <table id="resultTable">
          <thead>
            <tr>
              <th data-sort="idx" style="width:38px">#</th>
              <th class="sortable" data-sort="round">Round</th>
              <th class="sortable" data-sort="type">Type</th>
              <th class="sortable" data-sort="inst">Institute</th>
              <th class="sortable" data-sort="prog">Academic Program</th>
              <th class="sortable" data-sort="quota">Quota</th>
              <th class="sortable" data-sort="seat">Seat</th>
              <th class="sortable" data-sort="gender">Gender</th>
              <th class="sortable numcell" data-sort="open">Open</th>
              <th class="sortable numcell" data-sort="close">Close</th>
            </tr>
          </thead>
          <tbody id="resultBody"></tbody>
        </table>
      </div>
      <div class="footer-note">
        <b>How the match works:</b> shows every seat where your rank qualifies — closing rank ≥ your rank − 5% (small reach allowed). When more than 500 seats qualify, only the 500 sharpest cutoffs are shown — narrow further with the filters above. <b>Quotas</b> (HS / OS / AI / GO / JK / LA) are auto-gated against your home state. Sub-quotas — <b>UPTAC</b> (AF / TF / FF), <b>GGSIPU</b> (Defence / Jain / Kashmiri / Sikh), <b>JAC</b> (Defence / Single Girl / Kashmiri Migrant) — appear as small purple tags. Sources: <a href="https://josaa.admissions.nic.in" target="_blank">JoSAA</a> · <a href="https://admissions.nic.in/csabspl/" target="_blank">CSAB</a> · <a href="https://admissions.nic.in/UPTAC/" target="_blank">UPTAC</a> · <a href="https://admissions.nic.in/UPTAC/" target="_blank">GGSIPU</a> · <a href="https://jacdelhi.admissions.nic.in" target="_blank">JAC Delhi</a>.
      </div>
    </div>
  </div>

  <div id="emptyHero" class="hidden"></div>
</main>

<script>
const COLS = __COLS__;
const RAW = __DATA__;
const INST_STATE = __INST_STATE__;
const STATES = __STATES__;
const ROWS = RAW.map(r => { const o = {}; COLS.forEach((c,i)=>o[c]=r[i]); return o; });

const $ = id => document.getElementById(id);
const fmt = n => n==null ? '' : n.toLocaleString('en-IN');
const sanitize = s => String(s||'').replace(/[^a-z0-9]+/gi,'_');

function animateCount(el, target, dur=900){
  const start = performance.now();
  const initial = +el.textContent.replace(/,/g,'') || 0;
  function frame(t){
    const p = Math.min(1, (t - start) / dur);
    const eased = 1 - Math.pow(1 - p, 3);
    el.textContent = Math.round(initial + (target - initial) * eased).toLocaleString('en-IN');
    if (p < 1) requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
}

(function init(){
  const sel = $('homeState');
  STATES.forEach(s => { const o=document.createElement('option'); o.value=s; o.textContent=s; sel.appendChild(o); });
  sel.value = 'Uttar Pradesh';

  // Per-counselling counts (top + cards)
  const counts = ROWS.reduce((a, r) => { a[r.round] = (a[r.round]||0)+1; return a; }, {});
  ['JoSAA','CSAB','UPTAC','GGSIPU','JAC'].forEach(rd => {
    const c = counts[rd] || 0;
    $('c'+rd).textContent = c.toLocaleString('en-IN') + ' cutoffs';
  });
  // Animated hero counters
  setTimeout(() => {
    animateCount($('totalCount'), ROWS.length);
    animateCount($('announceCount'), ROWS.length);
    animateCount($('josaaCountTop'), counts['JoSAA']||0);
    animateCount($('csabCountTop'), counts['CSAB']||0);
    animateCount($('uptacCountTop'), counts['UPTAC']||0);
    animateCount($('ggsipuCountTop'), counts['GGSIPU']||0);
    animateCount($('jacCountTop'), counts['JAC']||0);
  }, 200);

  $('roundToggle').addEventListener('click', e => {
    const c = e.target.closest('.round-card'); if (!c) return;
    c.classList.toggle('on');
  });

  // Seat-pool radio behavior — keep #gender hidden input in sync.
  document.querySelectorAll('#genderGroup .radio-option').forEach(o => {
    o.addEventListener('click', () => setGender(o.dataset.value));
  });

  document.querySelectorAll('#resultTable th.sortable').forEach(th=>{
    th.addEventListener('click', ()=>{
      const k = th.dataset.sort; if (!k) return;
      currentSort = { key: k, dir: (currentSort.key===k ? -currentSort.dir : 1) };
      document.querySelectorAll('#resultTable th').forEach(x=>x.classList.remove('sort-asc','sort-desc'));
      th.classList.add(currentSort.dir===1?'sort-asc':'sort-desc');
      renderTable();
    });
  });

  ['quotaFilter','instFilter','search'].forEach(id => {
    $(id).addEventListener('change', renderTable);
    $(id).addEventListener('input', renderTable);
  });
  ['typeChips','srcChips'].forEach(id => {
    $(id).addEventListener('click', e => {
      const c = e.target.closest('.chip'); if (!c) return;
      c.classList.toggle('on'); renderTable();
    });
  });

  // Allow Enter in either rank field to predict
  $('crl').addEventListener('keydown', e => { if (e.key === 'Enter') runPredict(); });
  $('rank').addEventListener('keydown', e => { if (e.key === 'Enter') runPredict(); });
})();

let currentResults = [];
let totalQualifying = 0;
let currentSort = { key: 'close', dir: 1 };

function activeRounds(){
  return new Set([...document.querySelectorAll('#roundToggle .round-card.on')].map(c=>c.dataset.round));
}

function setGender(v){
  $('gender').value = v;
  document.querySelectorAll('#genderGroup .radio-option').forEach(o => {
    o.classList.toggle('selected', o.dataset.value === v);
  });
}

// Per-row rank: JoSAA uses category rank if entered; everything else
// (CSAB / UPTAC / GGSIPU / JAC) always uses CRL.
function rowRank(r, crl, categoryRank){
  if (r.round === 'JoSAA' && categoryRank) return categoryRank;
  return crl;
}

function computeEligible(seatType, gender, homeState){
  const eligibleGenders = gender==='F'
    ? new Set(['Gender-Neutral','Female-only (including Supernumerary)'])
    : new Set(['Gender-Neutral']);
  const rounds = activeRounds();
  return ROWS.filter(r => {
    if (!rounds.has(r.round)) return false;
    if (r.seat !== seatType) return false;
    if (!eligibleGenders.has(r.gender)) return false;
    const q = r.quota;
    if (q === 'AI') return true;
    if (q === 'HS') return INST_STATE[r.inst] === homeState;
    if (q === 'OS') return INST_STATE[r.inst] && INST_STATE[r.inst] !== homeState;
    if (q === 'JK') return homeState === 'Jammu & Kashmir';
    if (q === 'LA') return homeState === 'Ladakh';
    if (q === 'GO') return homeState === 'Goa';
    if (q === 'DASA-CIWG' || q === 'DASA-Non CIWG') return false;
    return false;
  });
}

// Show every seat where the rank actually qualifies (close rank within a 5%
// reach below the user's rank, no upper cap). When the qualifying set exceeds
// MAX_RESULTS, keep the sharpest cutoffs — the user's most aspirational picks.
const REACH_PCT = 5;
const MAX_RESULTS = 500;

function findInBandwidth(eligible, crl, categoryRank){
  let hits = eligible.filter(r => {
    const useRank = rowRank(r, crl, categoryRank);
    const lo = Math.max(1, Math.floor(useRank * (1 - REACH_PCT / 100)));
    return r.close >= lo;
  });
  const totalQualifying = hits.length;
  if (hits.length > MAX_RESULTS){
    hits = [...hits].sort((a,b)=>a.close-b.close).slice(0, MAX_RESULTS);
  }
  return { hits, tried: [{ scope: 'capped', total: totalQualifying, shown: hits.length }] };
}

function runPredict(){
  const name = $('name').value.trim();
  const phone = $('phone').value.trim();
  const email = $('email').value.trim();
  if (!name) { alert('Please enter your name — it is required.'); $('name').focus(); return; }
  if (!/^\d{10}$/.test(phone.replace(/\D/g, ''))) { alert('Please enter a valid 10-digit phone number.'); $('phone').focus(); return; }
  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { alert('Please enter a valid email — it is required.'); $('email').focus(); return; }
  const crl = parseInt($('crl').value || '0', 10);
  if (!crl || crl < 1) { alert('Please enter your JEE Main CRL — it is required.'); $('crl').focus(); return; }
  const categoryRankRaw = parseInt($('rank').value || '0', 10);
  const categoryRank = (categoryRankRaw && categoryRankRaw >= 1) ? categoryRankRaw : null;
  const seat = $('seatType').value;
  const gender = $('gender').value;
  const home = $('homeState').value;

  if (activeRounds().size === 0) { alert('Pick at least one counselling.'); return; }

  const eligible = computeEligible(seat, gender, home);
  const { hits, tried } = findInBandwidth(eligible, crl, categoryRank);

  currentResults = hits;
  totalQualifying = tried[0] && tried[0].total ? tried[0].total : hits.length;
  $('emptyHero').classList.add('hidden');
  $('resultsSection').classList.remove('hidden');
  buildFilters();
  renderTable();
  $('resultsSection').scrollIntoView({behavior:'smooth', block:'start'});
}

function buildFilters(){
  function fillMulti(id, values){
    const sel = $(id); sel.innerHTML = ''; sel.multiple = true; sel.size = 1;
    values.forEach(v=>{ const o=document.createElement('option'); o.value=v; o.textContent=v; o.selected=true; sel.appendChild(o); });
  }
  fillMulti('quotaFilter', [...new Set(currentResults.map(r=>r.quota))].sort());
  fillMulti('instFilter', [...new Set(currentResults.map(r=>r.inst))].sort());
  document.querySelectorAll('#typeChips .chip, #srcChips .chip').forEach(c=>c.classList.add('on'));
}

function resetFilters(){
  document.querySelectorAll('#typeChips .chip, #srcChips .chip').forEach(c=>c.classList.add('on'));
  ['quotaFilter','instFilter'].forEach(id=>{
    [...$(id).options].forEach(o=>o.selected=true);
  });
  $('search').value = '';
  renderTable();
}

function activeTypes(){ return new Set([...document.querySelectorAll('#typeChips .chip.on')].map(c=>c.dataset.type)); }
function activeSrcs(){ return new Set([...document.querySelectorAll('#srcChips .chip.on')].map(c=>c.dataset.src)); }
function selectedMulti(id){ return new Set([...$(id).selectedOptions].map(o=>o.value)); }

function filteredRows(){
  const types = activeTypes();
  const srcs = activeSrcs();
  const insts = selectedMulti('instFilter');
  const quotas = selectedMulti('quotaFilter');
  const q = ($('search').value||'').toLowerCase().trim();
  return currentResults.filter(r =>
    types.has(r.type) && srcs.has(r.round) &&
    insts.has(r.inst) && quotas.has(r.quota) &&
    (!q || r.inst.toLowerCase().includes(q) || r.prog.toLowerCase().includes(q))
  );
}

function sortRows(rows){
  const { key, dir } = currentSort;
  return [...rows].sort((a,b)=>{
    let av=a[key], bv=b[key];
    if (typeof av==='number' && typeof bv==='number') return (av-bv)*dir;
    return String(av).localeCompare(String(bv))*dir;
  });
}

function renderTable(){
  if (!currentResults.length) return;
  const rows = sortRows(filteredRows());
  const tb = $('resultBody');
  const shown = rows.length.toLocaleString('en-IN');
  const capped = totalQualifying > currentResults.length;
  $('visCount').textContent = capped
    ? `${shown} shown · ${totalQualifying.toLocaleString('en-IN')} qualify`
    : `${shown} options`;
  const frag = document.createDocumentFragment();
  rows.forEach((r,i)=>{
    const tr = document.createElement('tr');
    const roundPill = r.round === 'UPTAC' ? 'UPTAC-r' : r.round === 'GGSIPU' ? 'GGSIPU-r' : r.round === 'JAC' ? 'JAC-r' : r.round;
    const noteHtml = r.note ? `<span class="pill pill-note">${r.note}</span>` : '';
    tr.innerHTML = `
      <td>${i+1}</td>
      <td><span class="pill pill-${roundPill}">${r.round}</span></td>
      <td><span class="pill pill-${r.type}">${r.type}</span></td>
      <td>${r.inst}</td>
      <td>${r.prog}</td>
      <td><span class="pill pill-quota">${r.quota}</span>${noteHtml}</td>
      <td>${r.seat}</td>
      <td>${r.gender.replace(' (including Supernumerary)','')}</td>
      <td class="numcell">${fmt(r.open)}</td>
      <td class="numcell">${fmt(r.close)}</td>`;
    frag.appendChild(tr);
  });
  tb.innerHTML = '';
  tb.appendChild(frag);
}

function csvEsc(s){ s=String(s); return /[",\n]/.test(s) ? '"'+s.replace(/"/g,'""')+'"' : s; }

function exportPayload(){
  const rows = sortRows(filteredRows());
  const name = $('name').value.trim();
  const phone = $('phone').value.trim();
  const email = $('email').value.trim();
  const crl = $('crl').value;
  const rank = $('rank').value;
  const seat = $('seatType').value;
  const gen = $('gender').value==='F'?'Female':'Male';
  const hs = $('homeState').value;
  const budget = $('budget').value || 'No budget constraints';
  const meta = [
    ['Generated by','PRAYUSH Unified Predictor'],
    ['Student', name],
    ['Phone', phone || '—'],
    ['Email', email || '—'],
    ['JEE Main CRL', crl],
    ['Category Rank (JoSAA only)', rank || '—'],
    ['Category', seat], ['Gender', gen], ['Home State', hs],
    ['Budget for Full Course', budget],
    ['Generated at', new Date().toLocaleString('en-IN')],
    ['Sources', 'JoSAA 2025 R6 + CSAB Special 2025 R3 + UPTAC 2025 final + GGSIPU 2025 R3 + JAC Delhi 2025 R5'],
    [],
  ];
  const header = ['Pref #','Round','Type','Institute','Program','Quota','Sub-quota','Seat','Gender','Open','Close'];
  const body = rows.map((r,i)=>[i+1,r.round,r.type,r.inst,r.prog,r.quota,r.note,r.seat,r.gender.replace(' (including Supernumerary)',''),r.open,r.close]);
  const fileTag = rank || crl || 'rank';
  return { meta, header, body, name, fileTag };
}

function dl(blob, filename){
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  document.body.appendChild(a); a.click(); a.remove();
}

function downloadCSV(){
  const { meta, header, body, name, fileTag } = exportPayload();
  const lines = [];
  meta.forEach(m => lines.push(m.map(csvEsc).join(',')));
  lines.push(header.map(csvEsc).join(','));
  body.forEach(r => lines.push(r.map(csvEsc).join(',')));
  dl(new Blob([lines.join('\n')], {type:'text/csv;charset=utf-8'}),
     `prayush_${sanitize(name)||'student'}_${fileTag}.csv`);
}

function downloadXLSX(){
  const { meta, header, body, name, fileTag } = exportPayload();
  let html = '<html><head><meta charset="utf-8"></head><body><table border="1">';
  meta.forEach(m => html += '<tr>' + m.map(x=>`<td>${String(x||'')}</td>`).join('') + '</tr>');
  html += '<tr>' + header.map(h=>`<th style="background:#2563eb;color:#fff">${h}</th>`).join('') + '</tr>';
  body.forEach(r => html += '<tr>' + r.map((x,i)=>`<td${i>=9?' style="text-align:right"':''}>${x}</td>`).join('') + '</tr>');
  html += '</table></body></html>';
  dl(new Blob(['﻿'+html], {type:'application/vnd.ms-excel'}),
     `prayush_${sanitize(name)||'student'}_${fileTag}.xls`);
}

function downloadPDF(){
  const { meta, header, body, name } = exportPayload();
  const w = window.open('', '_blank');
  const rows = body.map(r=>`<tr>${r.map((x,j)=>`<td${j>=9?' style="text-align:right"':''}>${x}</td>`).join('')}</tr>`).join('');
  const metaHtml = meta.map(m => m.length ? `<div><b>${m[0]}:</b> ${m[1]||''}</div>` : '').join('');
  w.document.write(`<html><head><title>PRAYUSH preference list ${name||''}</title>
    <style>body{font-family:sans-serif;margin:20px;color:#222}h1{font-size:18px;margin:0 0 10px}
    .meta{font-size:12px;margin-bottom:14px;line-height:1.5}
    table{border-collapse:collapse;width:100%;font-size:11px}
    th,td{border:1px solid #888;padding:4px 6px}
    th{background:#2563eb;color:#fff;text-align:left}</style></head>
    <body><h1>PRAYUSH · Unified Counselling Preference List</h1>
    <div class="meta">${metaHtml}</div>
    <table><thead><tr>${header.map(h=>`<th>${h}</th>`).join('')}</tr></thead><tbody>${rows}</tbody></table>
    <script>setTimeout(()=>window.print(),300);<\/script></body></html>`);
  w.document.close();
}

function resetAll(){
  ['name','phone','email','crl','rank','search'].forEach(id=>$(id).value='');
  $('seatType').value = 'OPEN';
  setGender('M');
  $('homeState').value = 'Uttar Pradesh';
  $('budget').value = '';
  document.querySelectorAll('#roundToggle .round-card').forEach(c=>c.classList.add('on'));
  currentResults = [];
  $('resultsSection').classList.add('hidden');
  window.scrollTo({top: 0, behavior: 'smooth'});
}
</script>
</body>
</html>
"""

html = (HTML
        .replace("__COLS__", json.dumps(cols))
        .replace("__DATA__", json.dumps(data_arr, separators=(",", ":")))
        .replace("__INST_STATE__", json.dumps(INST_STATE))
        .replace("__STATES__", json.dumps(STATES)))

OUT.write_text(html, encoding="utf-8")
size_kb = OUT.stat().st_size / 1024
print(f"Wrote {OUT}  ({size_kb:,.0f} KB, {len(data_arr):,} rows)")
