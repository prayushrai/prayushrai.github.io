"""Build a single-file HTML college predictor from the scraped JoSAA CSV."""
import pandas as pd
import json

CSV = '/sessions/amazing-cool-knuth/mnt/outputs/josaa_2025_r6_all.csv'
OUT = '/sessions/amazing-cool-knuth/mnt/outputs/josaa_predictor.html'

# Institute -> State mapping for NITs (all 32) and GFTIs with HS/OS
INSTITUTE_STATE = {
    # NITs
    "Dr. B R Ambedkar National Institute of Technology, Jalandhar": "Punjab",
    "Indian Institute of Engineering Science and Technology, Shibpur": "West Bengal",
    "Malaviya National Institute of Technology Jaipur": "Rajasthan",
    "Maulana Azad National Institute of Technology Bhopal": "Madhya Pradesh",
    "Motilal Nehru National Institute of Technology Allahabad": "Uttar Pradesh",
    "National Institute of Technology  Agartala": "Tripura",
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
    # GFTIs with HS/OS quotas
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
    "Andaman & Nicobar Islands","Bihar","Dadra & Nagar Haveli and Daman & Diu","Lakshadweep","Ladakh"
})

df = pd.read_csv(CSV)
# Keep only the columns we need and rename for compact JSON keys
df = df[['Institute Type','Institute','Academic Program Name','Quota','Seat Type','Gender','Opening Rank (int)','Closing Rank (int)']]
df.columns = ['type','inst','prog','quota','seat','gender','open','close']
df = df.dropna(subset=['open','close'])
df['open'] = df['open'].astype(int)
df['close'] = df['close'].astype(int)

# Build rows as arrays for compactness
rows = df.to_dict(orient='records')
# Use compact array-of-arrays to shrink file size
cols = ['type','inst','prog','quota','seat','gender','open','close']
data_arr = [[r[c] for c in cols] for r in rows]
print(f"Rows: {len(data_arr)}")

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>JoSAA 2025 College Predictor (NIT / IIIT / GFTI)</title>
<style>
  * { box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f4f6f9; color: #1a1a1a; }
  h1 { margin: 0 0 6px; font-size: 22px; }
  .sub { color: #666; font-size: 13px; margin-bottom: 18px; }
  .card { background: #fff; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); padding: 16px 18px; margin-bottom: 14px; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; }
  label { display: block; font-size: 12px; font-weight: 600; color: #444; margin-bottom: 4px; }
  input, select { width: 100%; padding: 8px 10px; border: 1px solid #ccd0d5; border-radius: 6px; font-size: 14px; background: #fff; }
  input:focus, select:focus { outline: none; border-color: #3478f6; box-shadow: 0 0 0 3px rgba(52,120,246,0.15); }
  button { padding: 9px 18px; font-size: 14px; font-weight: 600; border: none; border-radius: 6px; cursor: pointer; background: #3478f6; color: #fff; }
  button:hover { background: #2563eb; }
  button.secondary { background: #eef2f7; color: #1a1a1a; }
  button.secondary:hover { background: #dee4ec; }
  .actions { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
  .stats { background: #eff6ff; border-left: 4px solid #3478f6; padding: 10px 14px; border-radius: 4px; font-size: 14px; margin-bottom: 14px; }
  .filters { display: flex; gap: 16px; flex-wrap: wrap; align-items: flex-end; }
  .filter-group { display: flex; flex-direction: column; gap: 4px; min-width: 140px; }
  .chip-row { display: flex; gap: 8px; flex-wrap: wrap; }
  .chip { display: inline-flex; align-items: center; gap: 6px; padding: 5px 10px; background: #eef2f7; border-radius: 16px; font-size: 12px; cursor: pointer; user-select: none; border: 1.5px solid transparent; }
  .chip.on { background: #3478f6; color: #fff; border-color: #3478f6; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th, td { padding: 8px 10px; text-align: left; border-bottom: 1px solid #eef0f3; }
  th { background: #f8fafc; font-weight: 600; color: #344; position: sticky; top: 0; cursor: pointer; user-select: none; }
  th:hover { background: #eef2f7; }
  tr:hover td { background: #fafbfd; }
  .numcell { text-align: right; font-variant-numeric: tabular-nums; }
  .tag { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; }
  .tag-NIT { background: #dcfce7; color: #065f46; }
  .tag-IIIT { background: #e0e7ff; color: #3730a3; }
  .tag-GFTI { background: #fef3c7; color: #92400e; }
  .tag-quota { background: #f1f5f9; color: #475569; }
  .hidden { display: none !important; }
  .table-wrap { max-height: 62vh; overflow: auto; border: 1px solid #e6e9ed; border-radius: 6px; }
  .pill { display: inline-block; padding: 2px 8px; background: #eff6ff; color: #1e40af; border-radius: 10px; font-size: 11px; font-weight: 600; margin-left: 4px; }
  .footer-note { font-size: 11px; color: #888; margin-top: 12px; }
  .filter-summary { font-size: 12px; color: #666; margin-top: 4px; }
</style>
</head>
<body>

<h1>JoSAA 2025 College Predictor</h1>
<div class="sub">Based on Round 6 (final) closing ranks for NITs, IIITs, and GFTIs &middot; Data scraped from josaa.admissions.nic.in</div>

<div class="card">
  <div class="grid">
    <div><label>Student Name (optional)</label><input id="name" placeholder="e.g. Ankit Sharma"></div>
    <div><label>Rank (category rank if applicable)</label><input id="rank" type="number" placeholder="e.g. 10000" min="1"></div>
    <div><label>Category / Seat Type</label>
      <select id="seatType">
        <option value="OPEN">OPEN</option>
        <option value="EWS">EWS</option>
        <option value="OBC-NCL">OBC-NCL</option>
        <option value="SC">SC</option>
        <option value="ST">ST</option>
        <option value="OPEN (PwD)">OPEN (PwD)</option>
        <option value="EWS (PwD)">EWS (PwD)</option>
        <option value="OBC-NCL (PwD)">OBC-NCL (PwD)</option>
        <option value="SC (PwD)">SC (PwD)</option>
        <option value="ST (PwD)">ST (PwD)</option>
      </select>
    </div>
    <div><label>Gender</label>
      <select id="gender">
        <option value="M">Male</option>
        <option value="F">Female</option>
      </select>
    </div>
    <div><label>Home State</label>
      <select id="homeState"></select>
    </div>
    <div><label>Minimum options to show</label><input id="minCount" type="number" value="100" min="10"></div>
    <div><label>Starting rank bandwidth</label>
      <select id="startBw">
        <option value="10">±10% (default)</option>
        <option value="5">±5%</option>
        <option value="15">±15%</option>
        <option value="20">±20%</option>
      </select>
    </div>
    <div style="align-self: end;"><button onclick="run()">Find Colleges</button></div>
  </div>
</div>

<div id="resultsSection" class="hidden">
  <div class="stats" id="stats"></div>

  <div class="card">
    <div class="filters">
      <div class="filter-group">
        <label>Institute Type</label>
        <div class="chip-row" id="typeChips">
          <div class="chip on" data-type="NIT">NIT</div>
          <div class="chip on" data-type="IIIT">IIIT</div>
          <div class="chip on" data-type="GFTI">GFTI</div>
        </div>
      </div>
      <div class="filter-group">
        <label>Institute</label>
        <select id="instFilter" multiple size="1" style="min-width:240px"></select>
        <div class="filter-summary" id="instSummary">All institutes</div>
      </div>
      <div class="filter-group">
        <label>Academic Program</label>
        <select id="progFilter" multiple size="1" style="min-width:240px"></select>
        <div class="filter-summary" id="progSummary">All programs</div>
      </div>
      <div class="filter-group">
        <label>Quota</label>
        <select id="quotaFilter" multiple size="1"></select>
      </div>
      <div class="filter-group">
        <label>Search</label>
        <input id="search" placeholder="institute / program...">
      </div>
      <div class="filter-group">
        <label>&nbsp;</label>
        <div class="actions">
          <button class="secondary" onclick="resetFilters()">Reset filters</button>
        </div>
      </div>
    </div>
  </div>

  <div class="card">
    <div class="actions" style="margin-bottom:10px;">
      <strong style="flex:1">Preference list <span id="visCount" class="pill">0</span></strong>
      <button onclick="downloadCSV()">Download CSV</button>
      <button onclick="downloadXLSX()">Download Excel</button>
      <button class="secondary" onclick="downloadPDF()">Print / Save PDF</button>
    </div>
    <div class="table-wrap">
      <table id="resultTable">
        <thead>
          <tr>
            <th data-sort="idx" style="width:40px">#</th>
            <th data-sort="type">Type</th>
            <th data-sort="inst">Institute</th>
            <th data-sort="prog">Academic Program</th>
            <th data-sort="quota">Quota</th>
            <th data-sort="seat">Seat Type</th>
            <th data-sort="gender">Gender</th>
            <th data-sort="open" class="numcell">Open</th>
            <th data-sort="close" class="numcell">Close</th>
          </tr>
        </thead>
        <tbody id="resultBody"></tbody>
      </table>
    </div>
  </div>

  <div class="footer-note">
    Logic: The tool starts with your chosen bandwidth (default ±10%) around your rank and expands it in steps until the number of options is at least the minimum you set (default 100). Quota rows (HS / OS / AI / JK / GO / LA) are auto-selected based on your home state.
  </div>
</div>

<script>
// -------- Embedded data --------
const COLS = __COLS__;
const DATA = __DATA__;
const INST_STATE = __INST_STATE__;
const STATES = __STATES__;
// -------------------------------

// Attach column names to rows as accessor
const ROWS = DATA.map(r => {
  const o = {}; COLS.forEach((c,i)=>o[c]=r[i]); return o;
});

// Populate home state dropdown
(function(){
  const sel = document.getElementById('homeState');
  STATES.forEach(s => { const o = document.createElement('option'); o.value = s; o.textContent = s; sel.appendChild(o); });
  sel.value = "Uttar Pradesh";
})();

let currentResults = [];   // results after bandwidth logic
let currentSort = {key:'close', dir:1}; // ascending close rank by default

function computeEligible(studentRank, seatType, gender, homeState) {
  const eligibleGenders = gender === 'F'
    ? new Set(['Gender-Neutral','Female-only (including Supernumerary)'])
    : new Set(['Gender-Neutral']);

  return ROWS.filter(r => {
    if (r.seat !== seatType) return false;
    if (!eligibleGenders.has(r.gender)) return false;
    // Quota gating
    const q = r.quota;
    if (q === 'AI') return true;
    if (q === 'HS') return INST_STATE[r.inst] === homeState;
    if (q === 'OS') return INST_STATE[r.inst] && INST_STATE[r.inst] !== homeState;
    if (q === 'JK') return homeState === 'Jammu & Kashmir';
    if (q === 'LA') return homeState === 'Ladakh';
    if (q === 'GO') return homeState === 'Goa';
    return false;
  });
}

function findInBandwidth(eligible, studentRank, startBwPct, minCount) {
  let bw = startBwPct;
  let hits = [];
  let tried = [];
  while (bw <= 500) {
    const lo = Math.max(1, Math.floor(studentRank * (1 - bw/100)));
    const hi = Math.ceil(studentRank * (1 + bw/100));
    hits = eligible.filter(r => r.close >= lo && r.close <= hi);
    tried.push({bw, lo, hi, count: hits.length});
    if (hits.length >= minCount) break;
    bw += 10;
  }
  // Fallback: if still short, show all where close >= rank (safeties) by nearest distance
  if (hits.length < minCount) {
    const extra = eligible
      .filter(r => !hits.includes(r))
      .map(r => ({...r, _d: Math.abs(r.close - studentRank)}))
      .sort((a,b)=>a._d-b._d)
      .slice(0, minCount - hits.length);
    hits = hits.concat(extra);
    tried.push({bw:'fallback-nearest', lo:null, hi:null, count: hits.length});
  }
  return {hits, tried};
}

function fmt(n){ return n==null?'':n.toLocaleString('en-IN'); }

function run() {
  const rank = parseInt(document.getElementById('rank').value || '0', 10);
  if (!rank || rank < 1) { alert('Enter a valid rank'); return; }
  const seatType = document.getElementById('seatType').value;
  const gender = document.getElementById('gender').value;
  const homeState = document.getElementById('homeState').value;
  const minCount = parseInt(document.getElementById('minCount').value || '100', 10);
  const startBw = parseInt(document.getElementById('startBw').value || '10', 10);

  const eligible = computeEligible(rank, seatType, gender, homeState);
  const {hits, tried} = findInBandwidth(eligible, rank, startBw, minCount);

  currentResults = hits;
  const finalStep = tried[tried.length-1];
  const usedBw = finalStep.bw;
  const loHi = (finalStep.lo!=null) ? `(ranks ${fmt(finalStep.lo)}–${fmt(finalStep.hi)})` : '(expanded by nearest rank)';

  const statsEl = document.getElementById('stats');
  statsEl.innerHTML = `
    Student rank <b>${fmt(rank)}</b> · ${seatType} · ${gender==='F'?'Female':'Male'} · Home state: <b>${homeState}</b><br>
    Eligible pool (before bandwidth): <b>${fmt(eligible.length)}</b> rows across the three institute types.<br>
    Final bandwidth used: <b>${typeof usedBw==='number' ? '±'+usedBw+'%' : usedBw}</b> ${loHi} · Options found: <b>${fmt(hits.length)}</b>.
  `;

  document.getElementById('resultsSection').classList.remove('hidden');
  buildFilters();
  renderTable();
}

function buildFilters() {
  // Type chips already exist. Build institute, program, quota dropdowns from currentResults.
  function fillMulti(selId, values) {
    const sel = document.getElementById(selId);
    sel.innerHTML = '';
    sel.multiple = true; sel.size = 1;
    values.forEach(v => {
      const o = document.createElement('option');
      o.value = v; o.textContent = v; o.selected = true;
      sel.appendChild(o);
    });
  }
  const insts = [...new Set(currentResults.map(r=>r.inst))].sort();
  const progs = [...new Set(currentResults.map(r=>r.prog))].sort();
  const quotas = [...new Set(currentResults.map(r=>r.quota))].sort();
  fillMulti('instFilter', insts);
  fillMulti('progFilter', progs);
  fillMulti('quotaFilter', quotas);

  document.getElementById('instSummary').textContent = `All ${insts.length} institutes`;
  document.getElementById('progSummary').textContent = `All ${progs.length} programs`;
}

function resetFilters() {
  document.querySelectorAll('#typeChips .chip').forEach(c=>c.classList.add('on'));
  ['instFilter','progFilter','quotaFilter'].forEach(id=>{
    const s = document.getElementById(id);
    [...s.options].forEach(o=>o.selected=true);
  });
  document.getElementById('search').value='';
  renderTable();
}

function activeTypes() {
  return new Set([...document.querySelectorAll('#typeChips .chip.on')].map(c=>c.dataset.type));
}
function selectedMulti(id){
  const s = document.getElementById(id);
  return new Set([...s.selectedOptions].map(o=>o.value));
}

function filteredRows() {
  const types = activeTypes();
  const insts = selectedMulti('instFilter');
  const progs = selectedMulti('progFilter');
  const quotas = selectedMulti('quotaFilter');
  const q = (document.getElementById('search').value||'').toLowerCase().trim();
  return currentResults.filter(r =>
    types.has(r.type) &&
    insts.has(r.inst) &&
    progs.has(r.prog) &&
    quotas.has(r.quota) &&
    (!q || r.inst.toLowerCase().includes(q) || r.prog.toLowerCase().includes(q))
  );
}

function sortRows(rows) {
  const {key, dir} = currentSort;
  return [...rows].sort((a,b)=>{
    let av=a[key], bv=b[key];
    if (typeof av==='number' && typeof bv==='number') return (av-bv)*dir;
    return String(av).localeCompare(String(bv))*dir;
  });
}

function renderTable() {
  const rows = sortRows(filteredRows());
  const tb = document.getElementById('resultBody');
  document.getElementById('visCount').textContent = rows.length.toLocaleString('en-IN');
  const frag = document.createDocumentFragment();
  rows.forEach((r,i)=>{
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${i+1}</td>
      <td><span class="tag tag-${r.type}">${r.type}</span></td>
      <td>${r.inst}</td>
      <td>${r.prog}</td>
      <td><span class="tag tag-quota">${r.quota}</span></td>
      <td>${r.seat}</td>
      <td>${r.gender.replace(' (including Supernumerary)','')}</td>
      <td class="numcell">${fmt(r.open)}</td>
      <td class="numcell">${fmt(r.close)}</td>`;
    frag.appendChild(tr);
  });
  tb.innerHTML = '';
  tb.appendChild(frag);
}

// Sort on header click
document.querySelectorAll('#resultTable th').forEach(th=>{
  th.addEventListener('click', ()=>{
    const k = th.dataset.sort;
    if (!k || k==='idx') return;
    currentSort = { key: k, dir: (currentSort.key===k ? -currentSort.dir : 1) };
    renderTable();
  });
});

// Chip toggle
document.getElementById('typeChips').addEventListener('click', e=>{
  if (e.target.classList.contains('chip')) {
    e.target.classList.toggle('on'); renderTable();
  }
});
['instFilter','progFilter','quotaFilter','search'].forEach(id=>{
  document.getElementById(id).addEventListener('change', renderTable);
  document.getElementById(id).addEventListener('input', renderTable);
});

// ---------- Downloads ----------
function csvEscape(s){ s=String(s); return /[",\n]/.test(s) ? '"'+s.replace(/"/g,'""')+'"' : s; }
function currentExportRows(){
  const rows = sortRows(filteredRows());
  const name = (document.getElementById('name').value||'').trim();
  const rank = document.getElementById('rank').value;
  const seat = document.getElementById('seatType').value;
  const gen = document.getElementById('gender').value==='F'?'Female':'Male';
  const hs = document.getElementById('homeState').value;
  const header = ['Preference #','Institute Type','Institute','Academic Program','Quota','Seat Type','Gender','Opening Rank','Closing Rank'];
  const meta = [
    ['Student Name', name],
    ['Rank', rank], ['Category', seat], ['Gender', gen], ['Home State', hs],
    ['Generated', new Date().toLocaleString('en-IN')],
    ['Source', 'JoSAA 2025 Round 6 (final) closing ranks'],
    []
  ];
  const body = rows.map((r,i)=>[i+1, r.type, r.inst, r.prog, r.quota, r.seat, r.gender.replace(' (including Supernumerary)',''), r.open, r.close]);
  return {meta, header, body, name, rank};
}

function downloadCSV(){
  const {meta, header, body, name, rank} = currentExportRows();
  const lines = [];
  meta.forEach(m => lines.push(m.map(csvEscape).join(',')));
  lines.push(header.map(csvEscape).join(','));
  body.forEach(r => lines.push(r.map(csvEscape).join(',')));
  const blob = new Blob([lines.join('\n')], {type:'text/csv;charset=utf-8'});
  triggerDownload(blob, `preference_list_${sanitize(name)||'student'}_${rank||'rank'}.csv`);
}

function downloadXLSX(){
  // Simple Excel-compatible: HTML table with .xls extension works in Excel
  const {meta, header, body, name, rank} = currentExportRows();
  let html = '<html><head><meta charset="utf-8"></head><body><table border="1">';
  meta.forEach(m => { html += '<tr>' + m.map(x=>`<td>${String(x||'')}</td>`).join('') + '</tr>'; });
  html += '<tr>' + header.map(h=>`<th style="background:#3478f6;color:#fff">${h}</th>`).join('') + '</tr>';
  body.forEach(r => { html += '<tr>' + r.map((x,i)=>`<td${i>=7?' style="text-align:right"':''}>${x}</td>`).join('') + '</tr>'; });
  html += '</table></body></html>';
  const blob = new Blob(['\ufeff'+html], {type:'application/vnd.ms-excel'});
  triggerDownload(blob, `preference_list_${sanitize(name)||'student'}_${rank||'rank'}.xls`);
}

function downloadPDF(){
  // Open a print-friendly window and invoke print dialog (user saves as PDF)
  const {meta, header, body, name, rank} = currentExportRows();
  const w = window.open('', '_blank');
  const rows = body.map((r,i)=>`<tr>${r.map((x,j)=>`<td${j>=7?' style="text-align:right"':''}>${x}</td>`).join('')}</tr>`).join('');
  const metaHtml = meta.map(m => m.length ? `<div><b>${m[0]}:</b> ${m[1]||''}</div>` : '').join('');
  w.document.write(`
    <html><head><title>Preference list ${name||''}</title>
    <style>
      body{font-family:sans-serif;margin:20px;color:#222}
      h1{font-size:18px;margin:0 0 10px}
      .meta{font-size:12px;margin-bottom:14px;line-height:1.5}
      table{border-collapse:collapse;width:100%;font-size:11px}
      th,td{border:1px solid #888;padding:4px 6px}
      th{background:#3478f6;color:#fff;text-align:left}
    </style></head>
    <body>
      <h1>JoSAA 2025 College Preference List</h1>
      <div class="meta">${metaHtml}</div>
      <table><thead><tr>${header.map(h=>`<th>${h}</th>`).join('')}</tr></thead>
      <tbody>${rows}</tbody></table>
      <script>window.onload=()=>window.print();<\/script>
    </body></html>`);
  w.document.close();
}

function triggerDownload(blob, filename){
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a'); a.href = url; a.download = filename;
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(()=>URL.revokeObjectURL(url), 2000);
}
function sanitize(s){ return String(s||'').replace(/[^a-z0-9_-]+/gi,'_').replace(/^_+|_+$/g,''); }
</script>
</body>
</html>
"""

html = (HTML_TEMPLATE
    .replace('__COLS__', json.dumps(cols))
    .replace('__DATA__', json.dumps(data_arr, separators=(',',':')))
    .replace('__INST_STATE__', json.dumps(INSTITUTE_STATE))
    .replace('__STATES__', json.dumps(STATES))
)

with open(OUT, 'w', encoding='utf-8') as f:
    f.write(html)
import os
print(f"Wrote {OUT} ({os.path.getsize(OUT):,} bytes)")
