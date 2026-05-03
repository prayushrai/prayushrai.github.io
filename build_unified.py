"""Build a single unified HTML predictor that merges JoSAA Round 6 + CSAB Special R3 cutoffs.

Output: unified_predictor.html (self-contained, no API, no external requests).
"""
import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).parent
JOSAA_CSV = ROOT / "josaa_2025_r6_all.csv"
CSAB_CSV = ROOT / "csab_2025_final_all.csv"
OUT = ROOT / "unified_predictor.html"

INSTITUTE_STATE = {
    # NITs (32)
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
    # GFTIs with state quotas
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

STATES = sorted(set(INSTITUTE_STATE.values()) | {
    "Andaman & Nicobar Islands", "Bihar", "Dadra & Nagar Haveli and Daman & Diu",
    "Lakshadweep", "Ladakh"
})

CSAB_QUOTA_MAP = {
    "All India": "AI",
    "Home State": "HS",
    "Other State": "OS",
    "Home State for Goa": "GO",
    "Jammu & Kashmir (UT)": "JK",
    "DASA-CIWG": "DASA-CIWG",
    "DASA-Non CIWG": "DASA-Non CIWG",
}


def load_and_tag(csv_path: Path, round_label: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df = df[["Institute Type", "Institute", "Academic Program Name",
             "Quota", "Seat Type", "Gender",
             "Opening Rank (int)", "Closing Rank (int)"]].copy()
    df.columns = ["type", "inst", "prog", "quota", "seat", "gender", "open", "close"]
    df = df.dropna(subset=["open", "close"])
    df["open"] = df["open"].astype(int)
    df["close"] = df["close"].astype(int)
    df["round"] = round_label
    return df


josaa = load_and_tag(JOSAA_CSV, "JoSAA")
csab = load_and_tag(CSAB_CSV, "CSAB")
csab["quota"] = csab["quota"].map(lambda q: CSAB_QUOTA_MAP.get(q, q))

merged = pd.concat([josaa, csab], ignore_index=True)
print(f"JoSAA: {len(josaa)}  CSAB: {len(csab)}  TOTAL: {len(merged)}")

cols = ["round", "type", "inst", "prog", "quota", "seat", "gender", "open", "close"]
data_arr = [[r[c] for c in cols] for r in merged.to_dict(orient="records")]

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PRAYUSH · Unified JEE Counselling Predictor</title>
<style>
  :root {
    --bg-0: #050616;
    --bg-1: #0a0e2a;
    --glass: rgba(255,255,255,0.045);
    --border: rgba(255,255,255,0.10);
    --text: #e7ecff;
    --text-dim: #9aa3c7;
    --text-faint: #6b7299;
    --accent: #7c5cff;
    --accent-2: #22d3ee;
    --accent-3: #ff6ec4;
    --green: #34d399;
    --orange: #fbbf24;
    --red: #fb7185;
    --josaa: #22d3ee;
    --csab: #ff6ec4;
  }
  * { box-sizing: border-box; }
  html, body { height: 100%; }
  body {
    margin: 0;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: var(--bg-0);
    color: var(--text);
    overflow-x: hidden;
    min-height: 100vh;
    position: relative;
  }
  .aurora {
    position: fixed; inset: 0; z-index: -2; overflow: hidden;
    background: radial-gradient(ellipse at top, #1a0f4a 0%, #050616 60%);
  }
  .aurora::before, .aurora::after {
    content: ''; position: absolute; width: 60vw; height: 60vw;
    border-radius: 50%; filter: blur(80px); opacity: 0.45;
    animation: float 18s ease-in-out infinite;
  }
  .aurora::before {
    top: -10vw; left: -10vw;
    background: radial-gradient(circle, var(--accent) 0%, transparent 70%);
  }
  .aurora::after {
    bottom: -20vw; right: -10vw;
    background: radial-gradient(circle, var(--accent-2) 0%, transparent 70%);
    animation-delay: -9s;
  }
  @keyframes float {
    0%, 100% { transform: translate(0, 0) scale(1); }
    50% { transform: translate(8vw, 6vw) scale(1.15); }
  }
  .grid-overlay {
    position: fixed; inset: 0; z-index: -1; pointer-events: none;
    background-image:
      linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px),
      linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px);
    background-size: 60px 60px;
    mask-image: radial-gradient(ellipse at center, black 30%, transparent 80%);
  }

  .shell { max-width: 1400px; margin: 0 auto; padding: 24px 28px 60px; }

  header.brand { display: flex; align-items: center; gap: 14px; margin-bottom: 6px; }
  .logo {
    width: 44px; height: 44px; border-radius: 12px;
    background: conic-gradient(from 0deg, var(--accent), var(--accent-2), var(--accent-3), var(--accent));
    position: relative; box-shadow: 0 0 30px rgba(124,92,255,0.45);
    animation: spin 12s linear infinite;
  }
  .logo::after {
    content: ''; position: absolute; inset: 4px; border-radius: 9px;
    background: var(--bg-0);
  }
  .logo span {
    position: absolute; inset: 0; display: flex; align-items: center; justify-content: center;
    font-weight: 800; font-size: 18px; z-index: 1;
    background: linear-gradient(135deg, var(--accent), var(--accent-2));
    -webkit-background-clip: text; background-clip: text; color: transparent;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  h1 {
    margin: 0; font-size: 28px; font-weight: 800; letter-spacing: -0.02em;
    background: linear-gradient(135deg, #fff 0%, #b9a4ff 60%, var(--accent-2) 100%);
    -webkit-background-clip: text; background-clip: text; color: transparent;
  }
  .tagline { color: var(--text-dim); font-size: 13px; margin: 4px 0 22px; letter-spacing: 0.02em; }
  .tagline b { color: var(--accent-2); }

  .glass {
    background: var(--glass);
    border: 1px solid var(--border);
    border-radius: 18px;
    backdrop-filter: blur(16px) saturate(150%);
    -webkit-backdrop-filter: blur(16px) saturate(150%);
    padding: 18px 20px;
    box-shadow: 0 8px 32px rgba(5,8,30,0.4), inset 0 1px 0 rgba(255,255,255,0.05);
  }

  .section-title { font-size: 11px; font-weight: 700; letter-spacing: 0.16em; text-transform: uppercase; color: var(--text-faint); margin: 0 0 12px; }

  .form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 12px; }
  label { display: block; font-size: 11px; font-weight: 600; color: var(--text-dim); margin-bottom: 5px; letter-spacing: 0.02em; }
  input, select {
    width: 100%; padding: 10px 12px;
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 10px;
    color: var(--text); font-size: 14px; font-family: inherit;
    transition: all 0.2s;
  }
  input:focus, select:focus {
    outline: none;
    border-color: var(--accent);
    background: rgba(124,92,255,0.08);
    box-shadow: 0 0 0 3px rgba(124,92,255,0.18);
  }
  select option { background: var(--bg-1); color: var(--text); }

  button {
    padding: 10px 18px; font-size: 13px; font-weight: 600; letter-spacing: 0.02em;
    border: none; border-radius: 10px; cursor: pointer; font-family: inherit;
    background: linear-gradient(135deg, var(--accent) 0%, #5b3fcc 100%);
    color: #fff;
    box-shadow: 0 4px 14px rgba(124,92,255,0.35);
    transition: transform 0.15s, box-shadow 0.15s;
  }
  button:hover { transform: translateY(-1px); box-shadow: 0 6px 20px rgba(124,92,255,0.5); }
  button:active { transform: translateY(0); }
  button.secondary {
    background: rgba(255,255,255,0.06); color: var(--text);
    box-shadow: none; border: 1px solid var(--border);
  }
  button.secondary:hover { background: rgba(255,255,255,0.1); }
  button.ghost {
    background: transparent; color: var(--text-dim);
    box-shadow: none; border: 1px solid var(--border);
  }
  button.cta {
    background: linear-gradient(135deg, var(--accent) 0%, var(--accent-2) 100%);
    box-shadow: 0 4px 22px rgba(34,211,238,0.35);
    font-size: 14px; padding: 12px 22px;
  }
  button.cta:hover { box-shadow: 0 8px 30px rgba(34,211,238,0.5); }

  .actions { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }

  .round-toggle { display: flex; gap: 8px; flex-wrap: wrap; }
  .round-chip {
    padding: 8px 14px; border-radius: 999px;
    background: rgba(255,255,255,0.04); border: 1.5px solid var(--border);
    font-size: 12px; font-weight: 600; cursor: pointer; user-select: none;
    transition: all 0.15s;
    display: inline-flex; align-items: center; gap: 8px;
  }
  .round-chip:hover { background: rgba(255,255,255,0.08); }
  .round-chip.on[data-round="JoSAA"] {
    background: rgba(34,211,238,0.15); border-color: var(--josaa); color: var(--josaa);
    box-shadow: 0 0 16px rgba(34,211,238,0.25);
  }
  .round-chip.on[data-round="CSAB"] {
    background: rgba(255,110,196,0.15); border-color: var(--csab); color: var(--csab);
    box-shadow: 0 0 16px rgba(255,110,196,0.25);
  }
  .round-chip .pulse { width: 6px; height: 6px; border-radius: 50%; background: currentColor; }

  .stats-strip {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 12px; margin-bottom: 14px;
  }
  .stat {
    background: var(--glass); border: 1px solid var(--border); border-radius: 14px;
    padding: 14px 16px; backdrop-filter: blur(12px);
  }
  .stat-label { font-size: 10px; text-transform: uppercase; letter-spacing: 0.15em; color: var(--text-faint); margin-bottom: 4px; }
  .stat-value { font-size: 22px; font-weight: 700; color: var(--text); letter-spacing: -0.01em; }
  .stat-sub { font-size: 11px; color: var(--text-dim); margin-top: 2px; }
  .stat .accent-josaa { color: var(--josaa); }
  .stat .accent-csab { color: var(--csab); }

  .filter-bar { display: flex; gap: 14px; flex-wrap: wrap; align-items: flex-end; margin-bottom: 12px; }
  .filter-group { display: flex; flex-direction: column; gap: 4px; min-width: 150px; }
  .chip-row { display: flex; gap: 8px; flex-wrap: wrap; }
  .chip {
    padding: 6px 12px; border-radius: 999px; font-size: 12px; font-weight: 600;
    background: rgba(255,255,255,0.05); border: 1.5px solid transparent;
    cursor: pointer; user-select: none; transition: all 0.15s;
    color: var(--text-dim);
  }
  .chip:hover { background: rgba(255,255,255,0.1); color: var(--text); }
  .chip.on {
    background: linear-gradient(135deg, rgba(124,92,255,0.25), rgba(34,211,238,0.18));
    border-color: var(--accent); color: #fff;
    box-shadow: 0 0 14px rgba(124,92,255,0.25);
  }

  .table-wrap {
    max-height: 64vh; overflow: auto;
    border-radius: 14px; border: 1px solid var(--border);
    background: rgba(0,0,0,0.18);
  }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  thead th {
    position: sticky; top: 0; z-index: 2;
    background: rgba(10,14,42,0.95); backdrop-filter: blur(8px);
    text-align: left; padding: 11px 12px;
    font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em;
    color: var(--text-dim); border-bottom: 1px solid var(--border);
    cursor: pointer; user-select: none; white-space: nowrap;
  }
  thead th:hover { color: var(--accent-2); }
  thead th.sortable::after { content: ' ⇅'; opacity: 0.3; font-size: 10px; }
  thead th.sort-asc::after { content: ' ↑'; opacity: 1; color: var(--accent-2); }
  thead th.sort-desc::after { content: ' ↓'; opacity: 1; color: var(--accent-2); }
  tbody td { padding: 10px 12px; border-bottom: 1px solid rgba(255,255,255,0.05); }
  tbody tr { transition: background 0.1s; }
  tbody tr:hover td { background: rgba(124,92,255,0.06); }
  td.numcell { text-align: right; font-variant-numeric: tabular-nums; font-weight: 600; }
  .pill { display: inline-block; padding: 2px 9px; border-radius: 10px; font-size: 10px; font-weight: 700; letter-spacing: 0.04em; text-transform: uppercase; }
  .pill-NIT { background: rgba(52,211,153,0.18); color: var(--green); }
  .pill-IIIT { background: rgba(124,92,255,0.22); color: #b9a4ff; }
  .pill-GFTI { background: rgba(251,191,36,0.18); color: var(--orange); }
  .pill-JoSAA { background: rgba(34,211,238,0.18); color: var(--josaa); border: 1px solid rgba(34,211,238,0.4); }
  .pill-CSAB { background: rgba(255,110,196,0.18); color: var(--csab); border: 1px solid rgba(255,110,196,0.4); }
  .pill-quota { background: rgba(255,255,255,0.07); color: var(--text-dim); }

  .toolbar { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; margin-bottom: 12px; }
  .toolbar .grow { flex: 1; }
  .vis-pill {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 5px 12px; border-radius: 999px;
    background: rgba(34,211,238,0.12); color: var(--accent-2);
    font-size: 12px; font-weight: 700;
  }

  .footer-note { font-size: 11px; color: var(--text-faint); margin-top: 16px; line-height: 1.6; }
  .footer-note a { color: var(--accent-2); text-decoration: none; }
  .footer-note a:hover { text-decoration: underline; }

  .hidden { display: none !important; }

  ::-webkit-scrollbar { width: 10px; height: 10px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 10px; }
  ::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.2); }
</style>
</head>
<body>
<div class="aurora"></div>
<div class="grid-overlay"></div>

<div class="shell">

  <header class="brand">
    <div class="logo"><span>P</span></div>
    <div>
      <h1>PRAYUSH · Unified Counselling Predictor</h1>
      <div class="tagline">JoSAA Round 6 + CSAB Special Round 3 · 2025 · <b>12,164 cutoffs</b> across NITs, IIITs, GFTIs</div>
    </div>
  </header>

  <div class="glass">
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

    <div style="margin-top:14px;">
      <label>Counselling rounds</label>
      <div class="round-toggle" id="roundToggle">
        <div class="round-chip on" data-round="JoSAA"><span class="pulse"></span> JoSAA · R6 (final)</div>
        <div class="round-chip on" data-round="CSAB"><span class="pulse"></span> CSAB · Special R3</div>
      </div>
    </div>

    <div class="actions" style="margin-top:18px;">
      <button class="cta" onclick="runPredict()">⚡ Predict Colleges</button>
      <button class="ghost" onclick="resetAll()">Reset</button>
    </div>
  </div>

  <div id="resultsSection" class="hidden" style="margin-top:18px;">
    <div class="stats-strip" id="statsStrip"></div>

    <div class="glass">
      <div class="section-title">Filters</div>
      <div class="filter-bar">
        <div class="filter-group">
          <label>Institute Type</label>
          <div class="chip-row" id="typeChips">
            <div class="chip on" data-type="NIT">NIT</div>
            <div class="chip on" data-type="IIIT">IIIT</div>
            <div class="chip on" data-type="GFTI">GFTI</div>
          </div>
        </div>
        <div class="filter-group">
          <label>Source Round</label>
          <div class="chip-row" id="srcChips">
            <div class="chip on" data-src="JoSAA">JoSAA</div>
            <div class="chip on" data-src="CSAB">CSAB</div>
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

    <div class="glass" style="margin-top:14px;">
      <div class="toolbar">
        <strong style="font-size:14px;">Your preference list</strong>
        <span class="vis-pill" id="visCount">0 options</span>
        <div class="grow"></div>
        <button class="secondary" onclick="downloadCSV()">⬇ CSV</button>
        <button class="secondary" onclick="downloadXLSX()">⬇ Excel</button>
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
        <b>How the bandwidth search works:</b> starts at your chosen ± window around the rank, then expands by 10% steps until it finds at least the minimum number of options. Quotas (HS / OS / AI / GO / JK / LA) are auto-gated against your home state. Source: <a href="https://josaa.admissions.nic.in" target="_blank">JoSAA</a> · <a href="https://admissions.nic.in/csabspl/" target="_blank">CSAB</a>.
      </div>
    </div>
  </div>

  <div id="emptyHero" class="glass" style="text-align:center;padding:50px 20px;margin-top:18px;">
    <div style="font-size:42px;margin-bottom:14px;background:linear-gradient(135deg,var(--accent),var(--accent-2),var(--accent-3));-webkit-background-clip:text;background-clip:text;color:transparent;">⚡</div>
    <div style="font-size:18px;font-weight:700;margin-bottom:6px;">Ready when you are</div>
    <div style="color:var(--text-dim);font-size:13px;max-width:560px;margin:0 auto;">
      Enter your category rank and PRAYUSH will surface every NIT / IIIT / GFTI seat where your rank stands a real chance — across both <b style="color:var(--josaa)">JoSAA</b> and <b style="color:var(--csab)">CSAB</b>.
    </div>
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

(function init(){
  const sel = $('homeState');
  STATES.forEach(s => { const o=document.createElement('option'); o.value=s; o.textContent=s; sel.appendChild(o); });
  sel.value = 'Uttar Pradesh';

  $('roundToggle').addEventListener('click', e => {
    const c = e.target.closest('.round-chip'); if (!c) return;
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
})();

let currentResults = [];
let currentSort = { key: 'close', dir: 1 };

function activeRounds(){
  return new Set([...document.querySelectorAll('#roundToggle .round-chip.on')].map(c=>c.dataset.round));
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

  if (activeRounds().size === 0) { alert('Pick at least one counselling round.'); return; }

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
  const bwTxt = (typeof final.bw === 'number') ? `±${final.bw}%` : final.bw;
  const range = (final.lo!=null) ? `(${fmt(final.lo)} – ${fmt(final.hi)})` : '';
  const josaaCount = currentResults.filter(r=>r.round==='JoSAA').length;
  const csabCount = currentResults.filter(r=>r.round==='CSAB').length;
  $('statsStrip').innerHTML = `
    <div class="stat"><div class="stat-label">Your Rank</div><div class="stat-value">${fmt(rank)}</div><div class="stat-sub">${seat} · ${gender==='F'?'Female':'Male'} · ${home}</div></div>
    <div class="stat"><div class="stat-label">Eligible Pool</div><div class="stat-value">${fmt(eligibleCount)}</div><div class="stat-sub">rows after quota & gender gates</div></div>
    <div class="stat"><div class="stat-label">Bandwidth Used</div><div class="stat-value">${bwTxt}</div><div class="stat-sub">${range}</div></div>
    <div class="stat"><div class="stat-label">Total Options</div><div class="stat-value">${fmt(currentResults.length)}</div><div class="stat-sub"><span class="accent-josaa">JoSAA ${josaaCount}</span> · <span class="accent-csab">CSAB ${csabCount}</span></div></div>
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
    tr.innerHTML = `
      <td>${i+1}</td>
      <td><span class="pill pill-${r.round}">${r.round}</span></td>
      <td><span class="pill pill-${r.type}">${r.type}</span></td>
      <td>${r.inst}</td>
      <td>${r.prog}</td>
      <td><span class="pill pill-quota">${r.quota}</span></td>
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
    ['Sources','JoSAA 2025 R6 + CSAB Special 2025 R3'], []
  ];
  const header = ['Pref #','Round','Type','Institute','Program','Quota','Seat','Gender','Open','Close'];
  const body = rows.map((r,i)=>[i+1,r.round,r.type,r.inst,r.prog,r.quota,r.seat,r.gender.replace(' (including Supernumerary)',''),r.open,r.close]);
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
  html += '<tr>' + header.map(h=>`<th style="background:#7c5cff;color:#fff">${h}</th>`).join('') + '</tr>';
  body.forEach(r => html += '<tr>' + r.map((x,i)=>`<td${i>=8?' style="text-align:right"':''}>${x}</td>`).join('') + '</tr>');
  html += '</table></body></html>';
  dl(new Blob(['﻿'+html], {type:'application/vnd.ms-excel'}),
     `prayush_${sanitize(name)||'student'}_${rank||'rank'}.xls`);
}

function downloadPDF(){
  const { meta, header, body, name } = exportPayload();
  const w = window.open('', '_blank');
  const rows = body.map(r=>`<tr>${r.map((x,j)=>`<td${j>=8?' style="text-align:right"':''}>${x}</td>`).join('')}</tr>`).join('');
  const metaHtml = meta.map(m => m.length ? `<div><b>${m[0]}:</b> ${m[1]||''}</div>` : '').join('');
  w.document.write(`<html><head><title>PRAYUSH preference list ${name||''}</title>
    <style>body{font-family:sans-serif;margin:20px;color:#222}h1{font-size:18px;margin:0 0 10px}
    .meta{font-size:12px;margin-bottom:14px;line-height:1.5}
    table{border-collapse:collapse;width:100%;font-size:11px}
    th,td{border:1px solid #888;padding:4px 6px}
    th{background:#7c5cff;color:#fff;text-align:left}</style></head>
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
  document.querySelectorAll('#roundToggle .round-chip').forEach(c=>c.classList.add('on'));
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
        .replace("__INST_STATE__", json.dumps(INSTITUTE_STATE))
        .replace("__STATES__", json.dumps(STATES)))

OUT.write_text(html, encoding="utf-8")
size_kb = OUT.stat().st_size / 1024
print(f"Wrote {OUT}  ({size_kb:,.0f} KB, {len(data_arr):,} rows)")
