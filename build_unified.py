"""Build the unified PRAYUSH predictor — JoSAA R6 + CSAB Special R3 + UPTAC final + GGSIPU R3.

Self-contained HTML output (index.html). No external requests at runtime.
"""
import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).parent
JOSAA_CSV = ROOT / "josaa_2025_r6_all.csv"
CSAB_CSV = ROOT / "csab_2025_final_all.csv"
UPTAC_CSV = ROOT / "UPTAC" / "uptac_2025_final.csv"
GGSIPU_CSV = ROOT / "ggsipu_2025_final.csv"
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


josaa = load_jc(JOSAA_CSV, "JoSAA")
csab = load_jc(CSAB_CSV, "CSAB")
csab["quota"] = csab["quota"].map(lambda q: CSAB_QUOTA_MAP.get(q, q))
uptac = load_uptac()
ggsipu = load_ggsipu()

merged = pd.concat([josaa, csab, uptac, ggsipu], ignore_index=True)
print(f"JoSAA: {len(josaa):,}  CSAB: {len(csab):,}  UPTAC: {len(uptac):,}  GGSIPU: {len(ggsipu):,}  TOTAL: {len(merged):,}")

# UPTAC = Uttar Pradesh, GGSIPU = Delhi for HS quota gating
INST_STATE = dict(NIT_GFTI_STATE)
for inst in uptac["inst"].unique():
    INST_STATE[inst] = "Uttar Pradesh"
for inst in ggsipu["inst"].unique():
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
<title>PRAYUSH · Unified JEE Counselling Predictor — JoSAA + CSAB + UPTAC + GGSIPU</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,700;9..144,900&family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">
<style>
  :root {
    --bg-0: #08061a;
    --bg-1: #110a2e;
    --bg-2: #1a0f3e;
    --ink: #f6f0ff;
    --ink-dim: #b8a9d9;
    --ink-faint: #7a6c9c;
    --line: rgba(255,255,255,0.09);
    --line-strong: rgba(255,255,255,0.18);
    --rose: #ff4d8b;
    --rose-2: #ff8fb1;
    --gold: #ffb547;
    --gold-2: #ffd470;
    --jade: #2dd4bf;
    --violet: #a855f7;
    --indigo: #818cf8;
    --plum: #c084fc;
    --josaa: #22d3ee;
    --csab: #ff4d8b;
    --uptac: #ffb547;
    --ggsipu: #a3e635;
  }
  * { box-sizing: border-box; }
  html, body { height: 100%; }
  body {
    margin: 0;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: var(--bg-0);
    color: var(--ink);
    overflow-x: hidden;
    min-height: 100vh;
    position: relative;
    -webkit-font-smoothing: antialiased;
  }

  /* === Mesh-gradient background === */
  .mesh {
    position: fixed; inset: 0; z-index: -3;
    background:
      radial-gradient(at 8% 12%, #ff4d8b22 0%, transparent 45%),
      radial-gradient(at 92% 18%, #ffb54722 0%, transparent 45%),
      radial-gradient(at 18% 88%, #a855f733 0%, transparent 50%),
      radial-gradient(at 78% 78%, #2dd4bf22 0%, transparent 45%),
      radial-gradient(at 38% 50%, #a3e63522 0%, transparent 50%),
      radial-gradient(at 50% 50%, #6366f122 0%, transparent 60%),
      linear-gradient(180deg, #0a0625 0%, #08061a 60%, #050414 100%);
  }
  .blob {
    position: fixed; z-index: -2;
    border-radius: 50%; filter: blur(90px); opacity: 0.55; pointer-events: none;
    will-change: transform;
  }
  .blob.b1 { top: -8vw; left: -10vw; width: 50vw; height: 50vw; background: radial-gradient(circle, var(--rose) 0%, transparent 70%); animation: drift1 22s ease-in-out infinite; }
  .blob.b2 { top: 10vw; right: -12vw; width: 45vw; height: 45vw; background: radial-gradient(circle, var(--gold) 0%, transparent 70%); animation: drift2 28s ease-in-out infinite; }
  .blob.b3 { bottom: -10vw; left: 25vw; width: 55vw; height: 55vw; background: radial-gradient(circle, var(--violet) 0%, transparent 70%); animation: drift3 32s ease-in-out infinite; }
  .blob.b4 { bottom: 5vw; right: 15vw; width: 30vw; height: 30vw; background: radial-gradient(circle, var(--jade) 0%, transparent 70%); animation: drift1 26s ease-in-out infinite reverse; opacity: 0.4; }
  .blob.b5 { top: 35vw; left: 38vw; width: 28vw; height: 28vw; background: radial-gradient(circle, var(--ggsipu) 0%, transparent 70%); animation: drift2 24s ease-in-out infinite reverse; opacity: 0.3; }
  @keyframes drift1 { 0%,100% { transform: translate(0,0) scale(1); } 50% { transform: translate(6vw,4vw) scale(1.18); } }
  @keyframes drift2 { 0%,100% { transform: translate(0,0) scale(1); } 50% { transform: translate(-5vw,8vw) scale(1.12); } }
  @keyframes drift3 { 0%,100% { transform: translate(0,0) scale(1); } 50% { transform: translate(4vw,-6vw) scale(0.9); } }

  /* film-grain noise overlay */
  .grain {
    position: fixed; inset: 0; z-index: -1; pointer-events: none; opacity: 0.4;
    background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='200' height='200'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 0.06 0'/></filter><rect width='200' height='200' filter='url(%23n)'/></svg>");
    mix-blend-mode: overlay;
  }

  .shell { max-width: 1440px; margin: 0 auto; padding: 28px 32px 80px; }

  /* === Header === */
  header.brand {
    display: flex; align-items: center; gap: 16px; margin-bottom: 36px;
  }
  .mark {
    width: 52px; height: 52px; position: relative; flex-shrink: 0;
  }
  .mark svg { width: 100%; height: 100%; filter: drop-shadow(0 4px 24px rgba(255,77,139,0.5)); animation: mark-spin 16s linear infinite; }
  @keyframes mark-spin { to { transform: rotate(360deg); } }
  .mark-name {
    font-family: 'Fraunces', Georgia, serif; font-weight: 900;
    font-size: 22px; letter-spacing: 0.01em;
    background: linear-gradient(135deg, #fff 0%, var(--rose-2) 50%, var(--gold-2) 100%);
    -webkit-background-clip: text; background-clip: text; color: transparent;
  }
  .mark-sub { font-size: 11px; color: var(--ink-faint); letter-spacing: 0.18em; text-transform: uppercase; margin-top: 2px; }
  .top-meta { margin-left: auto; display: flex; gap: 18px; align-items: center; flex-wrap: wrap; }
  .top-pill {
    display: inline-flex; align-items: center; gap: 8px;
    padding: 7px 14px; border-radius: 999px;
    background: rgba(255,255,255,0.05); border: 1px solid var(--line);
    font-size: 11px; font-weight: 600; color: var(--ink-dim);
    backdrop-filter: blur(10px);
  }
  .top-pill .dot { width: 6px; height: 6px; border-radius: 50%; box-shadow: 0 0 8px currentColor; }
  .top-pill.j { color: var(--josaa); } .top-pill.j .dot { background: var(--josaa); }
  .top-pill.c { color: var(--csab); } .top-pill.c .dot { background: var(--csab); }
  .top-pill.u { color: var(--uptac); } .top-pill.u .dot { background: var(--uptac); }
  .top-pill.g { color: var(--ggsipu); } .top-pill.g .dot { background: var(--ggsipu); }

  /* === Hero === */
  .hero { margin-bottom: 36px; max-width: 940px; }
  .hero h1 {
    font-family: 'Fraunces', Georgia, serif;
    font-weight: 900; font-size: clamp(40px, 6vw, 78px);
    line-height: 0.95; letter-spacing: -0.035em;
    margin: 0 0 18px;
    background: linear-gradient(120deg, #fff 0%, var(--rose-2) 30%, var(--gold-2) 55%, var(--jade) 80%, #fff 100%);
    background-size: 200% 100%;
    -webkit-background-clip: text; background-clip: text; color: transparent;
    animation: shimmer 8s ease-in-out infinite;
  }
  @keyframes shimmer { 0%,100% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } }
  .hero h1 .ital { font-style: italic; font-weight: 500; }
  .hero p {
    font-size: clamp(15px, 1.6vw, 18px); line-height: 1.55; color: var(--ink-dim);
    max-width: 700px; margin: 0;
  }
  .hero p b { color: #fff; font-weight: 600; }

  .stat-mini-row { display: flex; gap: 20px; margin-top: 22px; flex-wrap: wrap; }
  .stat-mini {
    display: flex; flex-direction: column; gap: 2px; padding-right: 22px; border-right: 1px solid var(--line);
  }
  .stat-mini:last-child { border-right: none; }
  .stat-mini .v {
    font-family: 'JetBrains Mono', monospace; font-weight: 700;
    font-size: 26px; letter-spacing: -0.02em;
  }
  .stat-mini .v.j { color: var(--josaa); }
  .stat-mini .v.c { color: var(--csab); }
  .stat-mini .v.u { color: var(--uptac); }
  .stat-mini .v.g { color: var(--ggsipu); }
  .stat-mini .v.t { background: linear-gradient(135deg, var(--rose-2), var(--gold-2)); -webkit-background-clip: text; background-clip: text; color: transparent; }
  .stat-mini .l { font-size: 10px; text-transform: uppercase; letter-spacing: 0.18em; color: var(--ink-faint); }

  /* === Glass cards === */
  .panel {
    background: linear-gradient(135deg, rgba(255,255,255,0.04), rgba(255,255,255,0.015));
    border: 1px solid var(--line); border-radius: 22px;
    backdrop-filter: blur(20px) saturate(180%);
    -webkit-backdrop-filter: blur(20px) saturate(180%);
    padding: 22px 24px;
    box-shadow: 0 10px 40px rgba(5,4,20,0.5), inset 0 1px 0 rgba(255,255,255,0.07);
    position: relative;
  }
  .panel::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.18), transparent);
    pointer-events: none;
  }
  .panel + .panel { margin-top: 16px; }

  .section-title {
    font-size: 10px; font-weight: 700; letter-spacing: 0.22em;
    text-transform: uppercase; color: var(--ink-faint); margin: 0 0 14px;
    display: flex; align-items: center; gap: 10px;
  }
  .section-title::before {
    content: ''; width: 18px; height: 1px;
    background: linear-gradient(90deg, var(--rose), transparent);
  }

  /* === Form === */
  .form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 14px; }
  label { display: block; font-size: 10px; font-weight: 700; color: var(--ink-faint); margin-bottom: 6px; letter-spacing: 0.12em; text-transform: uppercase; }
  input, select {
    width: 100%; padding: 12px 14px;
    background: rgba(255,255,255,0.035);
    border: 1px solid var(--line);
    border-radius: 12px;
    color: var(--ink); font-size: 14px; font-family: inherit; font-weight: 500;
    transition: all 0.18s;
  }
  input::placeholder { color: var(--ink-faint); }
  input:focus, select:focus {
    outline: none;
    border-color: var(--rose);
    background: rgba(255,77,139,0.06);
    box-shadow: 0 0 0 3px rgba(255,77,139,0.15);
  }
  select option { background: var(--bg-1); color: var(--ink); }

  /* === Buttons === */
  button {
    padding: 11px 20px; font-size: 13px; font-weight: 600; letter-spacing: 0.01em;
    border: none; border-radius: 12px; cursor: pointer; font-family: inherit;
    background: rgba(255,255,255,0.06); color: var(--ink);
    border: 1px solid var(--line);
    transition: all 0.18s;
  }
  button:hover { background: rgba(255,255,255,0.1); border-color: var(--line-strong); }
  button.ghost { background: transparent; color: var(--ink-dim); }
  button.ghost:hover { color: var(--ink); }

  button.cta {
    position: relative; overflow: hidden;
    padding: 14px 30px; font-size: 14px; font-weight: 700;
    background: linear-gradient(135deg, var(--rose) 0%, var(--gold) 100%);
    color: #1a0817; border: none;
    box-shadow: 0 8px 30px rgba(255,77,139,0.35), 0 4px 12px rgba(255,181,71,0.25);
    letter-spacing: 0.02em;
  }
  button.cta::before {
    content: ''; position: absolute; top: 0; left: -100%; width: 60%; height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.5), transparent);
    transform: skewX(-25deg);
    transition: left 0.7s;
  }
  button.cta:hover { transform: translateY(-2px); box-shadow: 0 14px 40px rgba(255,77,139,0.5), 0 6px 16px rgba(255,181,71,0.35); border: none; }
  button.cta:hover::before { left: 200%; }

  .actions { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }

  /* === Counselling round chips === */
  .round-row { display: flex; gap: 12px; flex-wrap: wrap; }
  .round-card {
    flex: 1; min-width: 200px;
    padding: 14px 16px; border-radius: 14px;
    background: rgba(255,255,255,0.03); border: 1.5px solid var(--line);
    cursor: pointer; user-select: none; transition: all 0.18s;
    position: relative; overflow: hidden;
  }
  .round-card::after {
    content: ''; position: absolute; inset: 0;
    background: var(--card-glow, transparent); opacity: 0;
    transition: opacity 0.2s; pointer-events: none;
  }
  .round-card.on::after { opacity: 0.16; }
  .round-card.on { border-width: 1.5px; box-shadow: 0 0 0 1px var(--card-color, var(--rose)), 0 8px 24px var(--card-glow-shadow, rgba(255,77,139,0.25)); }
  .round-card[data-round="JoSAA"] { --card-color: var(--josaa); --card-glow: var(--josaa); --card-glow-shadow: rgba(34,211,238,0.3); }
  .round-card[data-round="CSAB"]  { --card-color: var(--csab);  --card-glow: var(--csab);  --card-glow-shadow: rgba(255,77,139,0.3); }
  .round-card[data-round="UPTAC"] { --card-color: var(--uptac); --card-glow: var(--uptac); --card-glow-shadow: rgba(255,181,71,0.3); }
  .round-card[data-round="GGSIPU"] { --card-color: var(--ggsipu); --card-glow: var(--ggsipu); --card-glow-shadow: rgba(163,230,53,0.3); }
  .round-card .head { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }
  .round-card .name { font-weight: 700; font-size: 14px; letter-spacing: -0.01em; }
  .round-card.on[data-round="JoSAA"] .name { color: var(--josaa); }
  .round-card.on[data-round="CSAB"] .name { color: var(--csab); }
  .round-card.on[data-round="UPTAC"] .name { color: var(--uptac); }
  .round-card.on[data-round="GGSIPU"] .name { color: var(--ggsipu); }
  .round-card .name .check { font-size: 10px; opacity: 0; margin-left: auto; transition: opacity 0.15s; }
  .round-card.on .check { opacity: 1; }
  .round-card .desc { font-size: 11px; color: var(--ink-faint); }
  .round-card .count { font-family: 'JetBrains Mono', monospace; font-size: 11px; color: var(--ink-dim); margin-top: 6px; }

  /* === Stats strip === */
  .stats-strip {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 14px; margin-bottom: 16px;
  }
  .stat-card {
    background: linear-gradient(135deg, rgba(255,255,255,0.04), rgba(255,255,255,0.015));
    border: 1px solid var(--line); border-radius: 16px;
    padding: 18px 20px; backdrop-filter: blur(14px);
    position: relative; overflow: hidden;
  }
  .stat-card::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
    background: var(--accent-bar, linear-gradient(90deg, var(--rose), var(--gold)));
  }
  .stat-card.violet { --accent-bar: linear-gradient(90deg, var(--violet), var(--plum)); }
  .stat-card.jade { --accent-bar: linear-gradient(90deg, var(--jade), var(--josaa)); }
  .stat-card.gold { --accent-bar: linear-gradient(90deg, var(--gold), var(--rose)); }
  .stat-label { font-size: 10px; text-transform: uppercase; letter-spacing: 0.16em; color: var(--ink-faint); margin-bottom: 6px; font-weight: 700; }
  .stat-value { font-family: 'JetBrains Mono', monospace; font-size: 26px; font-weight: 700; color: var(--ink); letter-spacing: -0.02em; line-height: 1.1; }
  .stat-sub { font-size: 12px; color: var(--ink-dim); margin-top: 6px; line-height: 1.4; }
  .stat-sub .j { color: var(--josaa); font-weight: 600; }
  .stat-sub .c { color: var(--csab); font-weight: 600; }
  .stat-sub .u { color: var(--uptac); font-weight: 600; }
  .stat-sub .g { color: var(--ggsipu); font-weight: 600; }

  /* === Filter bar === */
  .filter-bar { display: flex; gap: 16px; flex-wrap: wrap; align-items: flex-end; }
  .filter-group { display: flex; flex-direction: column; gap: 4px; min-width: 150px; }

  .chip-row { display: flex; gap: 8px; flex-wrap: wrap; }
  .chip {
    padding: 7px 14px; border-radius: 999px; font-size: 12px; font-weight: 600;
    background: rgba(255,255,255,0.04); border: 1.5px solid transparent;
    cursor: pointer; user-select: none; transition: all 0.15s;
    color: var(--ink-dim); letter-spacing: 0.01em;
  }
  .chip:hover { background: rgba(255,255,255,0.09); color: var(--ink); }
  .chip.on {
    background: linear-gradient(135deg, rgba(255,77,139,0.18), rgba(255,181,71,0.14));
    border-color: var(--rose); color: #fff;
    box-shadow: 0 0 16px rgba(255,77,139,0.3);
  }
  .chip[data-src="JoSAA"].on { background: linear-gradient(135deg, rgba(34,211,238,0.2), rgba(34,211,238,0.08)); border-color: var(--josaa); color: var(--josaa); box-shadow: 0 0 16px rgba(34,211,238,0.3); }
  .chip[data-src="CSAB"].on  { background: linear-gradient(135deg, rgba(255,77,139,0.2), rgba(255,77,139,0.08)); border-color: var(--csab);  color: var(--csab);  box-shadow: 0 0 16px rgba(255,77,139,0.3); }
  .chip[data-src="UPTAC"].on { background: linear-gradient(135deg, rgba(255,181,71,0.2), rgba(255,181,71,0.08)); border-color: var(--uptac); color: var(--uptac); box-shadow: 0 0 16px rgba(255,181,71,0.3); }
  .chip[data-src="GGSIPU"].on { background: linear-gradient(135deg, rgba(163,230,53,0.2), rgba(163,230,53,0.08)); border-color: var(--ggsipu); color: var(--ggsipu); box-shadow: 0 0 16px rgba(163,230,53,0.3); }

  /* === Table === */
  .table-wrap {
    max-height: 65vh; overflow: auto;
    border-radius: 16px; border: 1px solid var(--line);
    background: linear-gradient(180deg, rgba(0,0,0,0.25), rgba(0,0,0,0.15));
  }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  thead th {
    position: sticky; top: 0; z-index: 2;
    background: rgba(17,10,46,0.96); backdrop-filter: blur(10px);
    text-align: left; padding: 13px 14px;
    font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.14em;
    color: var(--ink-faint); border-bottom: 1px solid var(--line);
    cursor: pointer; user-select: none; white-space: nowrap;
  }
  thead th:hover { color: var(--gold); }
  thead th.sortable::after { content: ' ⇅'; opacity: 0.3; font-size: 10px; }
  thead th.sort-asc::after { content: ' ↑'; opacity: 1; color: var(--gold); }
  thead th.sort-desc::after { content: ' ↓'; opacity: 1; color: var(--gold); }
  tbody td { padding: 11px 14px; border-bottom: 1px solid rgba(255,255,255,0.04); }
  tbody tr { transition: background 0.12s; }
  tbody tr:hover td { background: linear-gradient(90deg, rgba(255,77,139,0.06), rgba(255,181,71,0.04)); }
  td.numcell { text-align: right; font-family: 'JetBrains Mono', monospace; font-weight: 700; color: var(--ink); }

  .pill {
    display: inline-block; padding: 3px 10px; border-radius: 999px;
    font-size: 10px; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase;
    line-height: 1.4;
  }
  .pill-NIT   { background: rgba(45,212,191,0.18); color: var(--jade); }
  .pill-IIIT  { background: rgba(168,85,247,0.22); color: var(--plum); }
  .pill-GFTI  { background: rgba(255,181,71,0.18); color: var(--gold); }
  .pill-UPTAC { background: linear-gradient(135deg, rgba(255,181,71,0.25), rgba(255,77,139,0.15)); color: var(--gold); }
  .pill-GGSIPU { background: linear-gradient(135deg, rgba(163,230,53,0.25), rgba(34,211,238,0.10)); color: var(--ggsipu); }
  .pill-JoSAA { background: rgba(34,211,238,0.16); color: var(--josaa); border: 1px solid rgba(34,211,238,0.4); }
  .pill-CSAB  { background: rgba(255,77,139,0.16); color: var(--csab);  border: 1px solid rgba(255,77,139,0.4); }
  .pill-UPTAC-r { background: rgba(255,181,71,0.16); color: var(--uptac); border: 1px solid rgba(255,181,71,0.4); }
  .pill-GGSIPU-r { background: rgba(163,230,53,0.16); color: var(--ggsipu); border: 1px solid rgba(163,230,53,0.4); }
  .pill-quota { background: rgba(255,255,255,0.07); color: var(--ink-dim); }
  .pill-note { background: rgba(168,85,247,0.18); color: var(--plum); margin-left: 4px; }

  /* === Toolbar === */
  .toolbar { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; margin-bottom: 14px; }
  .toolbar .grow { flex: 1; }
  .vis-pill {
    display: inline-flex; align-items: center; gap: 8px;
    padding: 7px 14px; border-radius: 999px;
    background: linear-gradient(135deg, rgba(255,77,139,0.18), rgba(255,181,71,0.14));
    color: var(--rose-2); border: 1px solid rgba(255,77,139,0.3);
    font-family: 'JetBrains Mono', monospace; font-size: 12px; font-weight: 700;
  }

  .footer-note {
    font-size: 11px; color: var(--ink-faint); margin-top: 18px; line-height: 1.7;
    border-top: 1px solid var(--line); padding-top: 14px;
  }
  .footer-note b { color: var(--ink-dim); }
  .footer-note a { color: var(--gold); text-decoration: none; }
  .footer-note a:hover { color: var(--gold-2); }
  .footer-note .deva { font-family: 'Fraunces', serif; font-style: italic; color: var(--rose-2); }

  /* === Empty hero (initial state) === */
  .empty-hero {
    background: linear-gradient(135deg, rgba(255,255,255,0.03), rgba(255,77,139,0.04));
    border: 1px dashed var(--line); border-radius: 22px;
    padding: 60px 30px; text-align: center;
  }
  .empty-hero .icon {
    font-size: 56px; margin-bottom: 18px; line-height: 1;
    background: linear-gradient(135deg, var(--rose), var(--gold), var(--violet));
    -webkit-background-clip: text; background-clip: text; color: transparent;
    animation: pulse 3s ease-in-out infinite;
  }
  @keyframes pulse { 0%,100% { transform: scale(1); } 50% { transform: scale(1.1); } }
  .empty-hero h2 { font-family: 'Fraunces', serif; font-weight: 700; font-size: 28px; margin: 0 0 10px; letter-spacing: -0.02em; }
  .empty-hero p { color: var(--ink-dim); font-size: 14px; max-width: 600px; margin: 0 auto; line-height: 1.6; }
  .empty-hero p b { color: #fff; font-weight: 600; }

  .hidden { display: none !important; }

  ::-webkit-scrollbar { width: 10px; height: 10px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 10px; }
  ::-webkit-scrollbar-thumb:hover { background: rgba(255,77,139,0.3); }

  @media (max-width: 720px) {
    .shell { padding: 18px 16px 60px; }
    .hero h1 { font-size: 38px; }
    .top-meta { width: 100%; justify-content: flex-start; margin-left: 0; margin-top: 4px; }
    header.brand { flex-wrap: wrap; }
  }
</style>
</head>
<body>
<div class="mesh"></div>
<div class="blob b1"></div>
<div class="blob b2"></div>
<div class="blob b3"></div>
<div class="blob b4"></div>
<div class="blob b5"></div>
<div class="grain"></div>

<div class="shell">

  <header class="brand">
    <div class="mark">
      <svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="g1" x1="0" y1="0" x2="64" y2="64">
            <stop offset="0%" stop-color="#ff4d8b"/>
            <stop offset="50%" stop-color="#ffb547"/>
            <stop offset="100%" stop-color="#a855f7"/>
          </linearGradient>
        </defs>
        <circle cx="32" cy="32" r="28" stroke="url(#g1)" stroke-width="2.5" fill="none"/>
        <path d="M 32 6 L 38 26 L 58 32 L 38 38 L 32 58 L 26 38 L 6 32 L 26 26 Z" fill="url(#g1)" opacity="0.95"/>
        <circle cx="32" cy="32" r="4" fill="#08061a"/>
      </svg>
    </div>
    <div>
      <div class="mark-name">PRAYUSH</div>
      <div class="mark-sub">JEE Counselling Atlas · 2025</div>
    </div>
    <div class="top-meta">
      <div class="top-pill j"><span class="dot"></span>JoSAA · R6</div>
      <div class="top-pill c"><span class="dot"></span>CSAB · Special</div>
      <div class="top-pill u"><span class="dot"></span>UPTAC · Final</div>
      <div class="top-pill g"><span class="dot"></span>GGSIPU · R3</div>
    </div>
  </header>

  <section class="hero">
    <h1>Every seat,<br><span class="ital">one search.</span></h1>
    <p>From <b>NIT Trichy</b> to <b>IPU Dwarka</b> — PRAYUSH unifies <b>JoSAA Round 6</b>, <b>CSAB Special Round 3</b>, <b>UPTAC final round</b>, and <b>GGSIPU Round 3</b> cutoffs into a single ranked predictor. Type your JEE Main rank. Walk away with a defensible choice list.</p>
    <div class="stat-mini-row">
      <div class="stat-mini"><div class="v t" id="totalCount">0</div><div class="l">Total Cutoffs</div></div>
      <div class="stat-mini"><div class="v j" id="josaaCountTop">0</div><div class="l">JoSAA</div></div>
      <div class="stat-mini"><div class="v c" id="csabCountTop">0</div><div class="l">CSAB</div></div>
      <div class="stat-mini"><div class="v u" id="uptacCountTop">0</div><div class="l">UPTAC</div></div>
      <div class="stat-mini"><div class="v g" id="ggsipuCountTop">0</div><div class="l">GGSIPU</div></div>
    </div>
  </section>

  <div class="panel">
    <div class="section-title">Your Profile</div>
    <div class="form-grid">
      <div><label>Name (optional)</label><input id="name" placeholder="e.g. Ankit Sharma"></div>
      <div><label>Category Rank</label><input id="rank" type="number" placeholder="e.g. 12000" min="1"></div>
      <div><label>Category</label>
        <select id="seatType">
          <option>OPEN</option><option>EWS</option><option>OBC-NCL</option>
          <option>SC</option><option>ST</option>
          <option>OPEN (PwD)</option><option>EWS (PwD)</option>
          <option>OBC-NCL (PwD)</option><option>SC (PwD)</option><option>ST (PwD)</option>
        </select>
      </div>
      <div><label>Gender</label>
        <select id="gender"><option value="M">Male</option><option value="F">Female</option></select>
      </div>
      <div><label>Home State</label><select id="homeState"></select></div>
      <div><label>Min options</label><input id="minCount" type="number" value="120" min="10"></div>
      <div><label>Initial bandwidth</label>
        <select id="startBw">
          <option value="10">±10% (default)</option>
          <option value="5">±5%</option>
          <option value="15">±15%</option>
          <option value="20">±20%</option>
        </select>
      </div>
    </div>

    <div style="margin-top:18px;">
      <label>Counsellings to include</label>
      <div class="round-row" id="roundToggle">
        <div class="round-card on" data-round="JoSAA">
          <div class="head"><div class="name">JoSAA <span class="check">✓</span></div></div>
          <div class="desc">Round 6 · NITs · IIITs · GFTIs · the main central counselling.</div>
          <div class="count" id="cJoSAA">0 cutoffs</div>
        </div>
        <div class="round-card on" data-round="CSAB">
          <div class="head"><div class="name">CSAB Special <span class="check">✓</span></div></div>
          <div class="desc">Special round 3 · vacant seats after JoSAA · second chance.</div>
          <div class="count" id="cCSAB">0 cutoffs</div>
        </div>
        <div class="round-card on" data-round="UPTAC">
          <div class="head"><div class="name">UPTAC <span class="check">✓</span></div></div>
          <div class="desc">Final round · UP state &amp; private engineering colleges (AKTU).</div>
          <div class="count" id="cUPTAC">0 cutoffs</div>
        </div>
        <div class="round-card on" data-round="GGSIPU">
          <div class="head"><div class="name">GGSIPU <span class="check">✓</span></div></div>
          <div class="desc">Round 3 (final) · IPU-affiliated B.Tech colleges in Delhi.</div>
          <div class="count" id="cGGSIPU">0 cutoffs</div>
        </div>
      </div>
    </div>

    <div class="actions" style="margin-top:22px;">
      <button class="cta" onclick="runPredict()">⚡ Predict My Colleges</button>
      <button class="ghost" onclick="resetAll()">Reset</button>
    </div>
  </div>

  <div id="resultsSection" class="hidden" style="margin-top:18px;">
    <div class="stats-strip" id="statsStrip"></div>

    <div class="panel">
      <div class="section-title">Filters</div>
      <div class="filter-bar">
        <div class="filter-group">
          <label>Institute Type</label>
          <div class="chip-row" id="typeChips">
            <div class="chip on" data-type="NIT">NIT</div>
            <div class="chip on" data-type="IIIT">IIIT</div>
            <div class="chip on" data-type="GFTI">GFTI</div>
            <div class="chip on" data-type="UPTAC">UPTAC</div>
            <div class="chip on" data-type="GGSIPU">GGSIPU</div>
          </div>
        </div>
        <div class="filter-group">
          <label>Source Round</label>
          <div class="chip-row" id="srcChips">
            <div class="chip on" data-src="JoSAA">JoSAA</div>
            <div class="chip on" data-src="CSAB">CSAB</div>
            <div class="chip on" data-src="UPTAC">UPTAC</div>
            <div class="chip on" data-src="GGSIPU">GGSIPU</div>
          </div>
        </div>
        <div class="filter-group">
          <label>Quota</label>
          <select id="quotaFilter" multiple size="1" style="min-width:170px"></select>
        </div>
        <div class="filter-group">
          <label>Institute</label>
          <select id="instFilter" multiple size="1" style="min-width:240px"></select>
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
        <strong style="font-size:14px; font-family:'Fraunces',serif; font-weight:700;">Your preference list</strong>
        <span class="vis-pill" id="visCount">0 options</span>
        <div class="grow"></div>
        <button onclick="downloadCSV()">⬇ CSV</button>
        <button onclick="downloadXLSX()">⬇ Excel</button>
        <button class="ghost" onclick="downloadPDF()">🖨 Print / PDF</button>
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
        <b>How the bandwidth search works:</b> starts at your chosen ± window around the rank, then expands by 10% steps until it finds at least the minimum number of options. <b>Quotas</b> (HS / OS / AI / GO / JK / LA) are auto-gated against your home state. <b>UPTAC</b> sub-quotas (AF / TF / FF) and <b>GGSIPU</b> sub-quotas (Defence / Jain / Kashmiri / Sikh) appear as small purple tags. <span class="deva">शुभकामनाएँ</span> · Sources: <a href="https://josaa.admissions.nic.in" target="_blank">JoSAA</a> · <a href="https://admissions.nic.in/csabspl/" target="_blank">CSAB</a> · <a href="https://admissions.nic.in/UPTAC/" target="_blank">UPTAC</a> · <a href="https://admissions.nic.in/UPTAC/" target="_blank">GGSIPU</a>.
      </div>
    </div>
  </div>

  <div id="emptyHero" class="empty-hero" style="margin-top:22px;">
    <div class="icon">✦</div>
    <h2>Ready when you are</h2>
    <p>Enter your JEE Main rank and PRAYUSH will surface every NIT, IIIT, GFTI, UPTAC, and GGSIPU seat where your rank stands a real chance — across <b style="color:var(--josaa)">JoSAA</b>, <b style="color:var(--csab)">CSAB</b>, <b style="color:var(--uptac)">UPTAC</b>, and <b style="color:var(--ggsipu)">GGSIPU</b> in one ranked list.</p>
  </div>

</div>

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
  ['JoSAA','CSAB','UPTAC','GGSIPU'].forEach(rd => {
    const c = counts[rd] || 0;
    $('c'+rd).textContent = c.toLocaleString('en-IN') + ' cutoffs';
  });
  // Animated hero counters
  setTimeout(() => {
    animateCount($('totalCount'), ROWS.length);
    animateCount($('josaaCountTop'), counts['JoSAA']||0);
    animateCount($('csabCountTop'), counts['CSAB']||0);
    animateCount($('uptacCountTop'), counts['UPTAC']||0);
    animateCount($('ggsipuCountTop'), counts['GGSIPU']||0);
  }, 200);

  $('roundToggle').addEventListener('click', e => {
    const c = e.target.closest('.round-card'); if (!c) return;
    c.classList.toggle('on');
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

  // Allow Enter in rank field to predict
  $('rank').addEventListener('keydown', e => { if (e.key === 'Enter') runPredict(); });
})();

let currentResults = [];
let currentSort = { key: 'close', dir: 1 };

function activeRounds(){
  return new Set([...document.querySelectorAll('#roundToggle .round-card.on')].map(c=>c.dataset.round));
}

function computeEligible(rank, seatType, gender, homeState){
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

function findInBandwidth(eligible, rank, startBw, minCount){
  let bw = startBw, hits = [], tried = [];
  while (bw <= 500){
    const lo = Math.max(1, Math.floor(rank * (1 - bw/100)));
    const hi = Math.ceil(rank * (1 + bw/100));
    hits = eligible.filter(r => r.close >= lo && r.close <= hi);
    tried.push({ bw, lo, hi, count: hits.length });
    if (hits.length >= minCount) break;
    bw += 10;
  }
  if (hits.length < minCount){
    const extra = eligible
      .filter(r => !hits.includes(r))
      .map(r => ({...r, _d: Math.abs(r.close - rank)}))
      .sort((a,b)=>a._d-b._d)
      .slice(0, minCount - hits.length);
    hits = hits.concat(extra);
    tried.push({ bw:'fallback-nearest', count: hits.length });
  }
  return { hits, tried };
}

function runPredict(){
  const rank = parseInt($('rank').value || '0', 10);
  if (!rank || rank < 1) { alert('Please enter a valid category rank.'); return; }
  const seat = $('seatType').value;
  const gender = $('gender').value;
  const home = $('homeState').value;
  const minCount = parseInt($('minCount').value || '120', 10);
  const startBw = parseInt($('startBw').value || '10', 10);

  if (activeRounds().size === 0) { alert('Pick at least one counselling.'); return; }

  const eligible = computeEligible(rank, seat, gender, home);
  const { hits, tried } = findInBandwidth(eligible, rank, startBw, minCount);

  currentResults = hits;
  $('emptyHero').classList.add('hidden');
  $('resultsSection').classList.remove('hidden');
  renderStats(rank, seat, gender, home, eligible.length, tried);
  buildFilters();
  renderTable();
  $('resultsSection').scrollIntoView({behavior:'smooth', block:'start'});
}

function renderStats(rank, seat, gender, home, eligibleCount, tried){
  const final = tried[tried.length-1];
  const bwTxt = (typeof final.bw === 'number') ? `±${final.bw}%` : 'expanded';
  const range = (final.lo!=null) ? `(${fmt(final.lo)} – ${fmt(final.hi)})` : '';
  const counts = currentResults.reduce((a,r)=>{ a[r.round]=(a[r.round]||0)+1; return a; }, {});
  $('statsStrip').innerHTML = `
    <div class="stat-card"><div class="stat-label">Your Rank</div><div class="stat-value">${fmt(rank)}</div><div class="stat-sub">${seat} · ${gender==='F'?'Female':'Male'} · ${home}</div></div>
    <div class="stat-card violet"><div class="stat-label">Eligible Pool</div><div class="stat-value">${fmt(eligibleCount)}</div><div class="stat-sub">rows after quota &amp; gender gates</div></div>
    <div class="stat-card gold"><div class="stat-label">Bandwidth Used</div><div class="stat-value">${bwTxt}</div><div class="stat-sub">${range || 'nearest-rank fallback'}</div></div>
    <div class="stat-card jade"><div class="stat-label">Total Options</div><div class="stat-value">${fmt(currentResults.length)}</div><div class="stat-sub"><span class="j">JoSAA ${counts['JoSAA']||0}</span> · <span class="c">CSAB ${counts['CSAB']||0}</span> · <span class="u">UPTAC ${counts['UPTAC']||0}</span> · <span class="g">GGSIPU ${counts['GGSIPU']||0}</span></div></div>
  `;
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
  $('visCount').textContent = `${rows.length.toLocaleString('en-IN')} options`;
  const frag = document.createDocumentFragment();
  rows.forEach((r,i)=>{
    const tr = document.createElement('tr');
    const roundPill = r.round === 'UPTAC' ? 'UPTAC-r' : r.round === 'GGSIPU' ? 'GGSIPU-r' : r.round;
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
  const rank = $('rank').value;
  const seat = $('seatType').value;
  const gen = $('gender').value==='F'?'Female':'Male';
  const hs = $('homeState').value;
  const meta = [
    ['Generated by','PRAYUSH Unified Predictor'],
    ['Student',name], ['Rank',rank], ['Category',seat], ['Gender',gen], ['Home State',hs],
    ['Generated at', new Date().toLocaleString('en-IN')],
    ['Sources','JoSAA 2025 R6 + CSAB Special 2025 R3 + UPTAC 2025 final'], []
  ];
  const header = ['Pref #','Round','Type','Institute','Program','Quota','Sub-quota','Seat','Gender','Open','Close'];
  const body = rows.map((r,i)=>[i+1,r.round,r.type,r.inst,r.prog,r.quota,r.note,r.seat,r.gender.replace(' (including Supernumerary)',''),r.open,r.close]);
  return { meta, header, body, name, rank };
}

function dl(blob, filename){
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  document.body.appendChild(a); a.click(); a.remove();
}

function downloadCSV(){
  const { meta, header, body, name, rank } = exportPayload();
  const lines = [];
  meta.forEach(m => lines.push(m.map(csvEsc).join(',')));
  lines.push(header.map(csvEsc).join(','));
  body.forEach(r => lines.push(r.map(csvEsc).join(',')));
  dl(new Blob([lines.join('\n')], {type:'text/csv;charset=utf-8'}),
     `prayush_${sanitize(name)||'student'}_${rank||'rank'}.csv`);
}

function downloadXLSX(){
  const { meta, header, body, name, rank } = exportPayload();
  let html = '<html><head><meta charset="utf-8"></head><body><table border="1">';
  meta.forEach(m => html += '<tr>' + m.map(x=>`<td>${String(x||'')}</td>`).join('') + '</tr>');
  html += '<tr>' + header.map(h=>`<th style="background:#ff4d8b;color:#fff">${h}</th>`).join('') + '</tr>';
  body.forEach(r => html += '<tr>' + r.map((x,i)=>`<td${i>=9?' style="text-align:right"':''}>${x}</td>`).join('') + '</tr>');
  html += '</table></body></html>';
  dl(new Blob(['﻿'+html], {type:'application/vnd.ms-excel'}),
     `prayush_${sanitize(name)||'student'}_${rank||'rank'}.xls`);
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
    th{background:#ff4d8b;color:#fff;text-align:left}</style></head>
    <body><h1>PRAYUSH · Unified Counselling Preference List</h1>
    <div class="meta">${metaHtml}</div>
    <table><thead><tr>${header.map(h=>`<th>${h}</th>`).join('')}</tr></thead><tbody>${rows}</tbody></table>
    <script>setTimeout(()=>window.print(),300);<\/script></body></html>`);
  w.document.close();
}

function resetAll(){
  ['name','rank','search'].forEach(id=>$(id).value='');
  $('seatType').value = 'OPEN';
  $('gender').value = 'M';
  $('homeState').value = 'Uttar Pradesh';
  $('minCount').value = '120';
  $('startBw').value = '10';
  document.querySelectorAll('#roundToggle .round-card').forEach(c=>c.classList.add('on'));
  currentResults = [];
  $('resultsSection').classList.add('hidden');
  $('emptyHero').classList.remove('hidden');
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
