"""Extract GGSIPU 2025 BTECH Round-3 cutoffs from the scanned PDF.

Strategy: render each page to high-DPI PNG, OCR the WHOLE page once with
Tesseract's image_to_data (returns every word with a bounding box), then
assign each word to a cell in the detected grid. Parse "Min Rank" /
"Max Rank" pairs from each cell.

Single full-page OCR is dramatically faster than per-cell calls (Tesseract
startup is ~250ms per invocation; we have ~3000 cells, so per-cell would
take 12+ minutes vs. ~10s per page for full-page mode).

Column codes (decoded from the appendix on page 8):
    NOJNAI  Jain Minority
    NOKMAI  Kashmiri Migrant
    NOSMAI  Sikh Minority
    BCDFHS  Delhi OBC Defence
    BCNOHS  Delhi OBC
    EWNOHS  Delhi EWS
    OPDFHS  Delhi General Defence
    OPNOHS  Delhi General (OPEN)
    OPPHHS  Delhi General PWD
    SCDFHS  Delhi SC Defence
    SCNOHS  Delhi SC
    STNOHS  Delhi ST
    EWNOOS  Outside-Delhi EWS
    OPDFOS  Outside-Delhi General Defence
    OPNOOS  Outside-Delhi General (OPEN)
    OPPHOS  Outside-Delhi General PWD
    SCDFOS  Outside-Delhi SC Defence
    SCNOOS  Outside-Delhi SC
    STNOOS  Outside-Delhi ST
    STPHOS  Outside-Delhi ST PWD
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
import pytesseract
from PIL import Image

ROOT = Path(__file__).parent
PDF = ROOT / "GGSIPU.pdf"
WORK = Path("/tmp/ggsipu_extract")
OUT_CSV = ROOT / "ggsipu_2025_final.csv"
DPI = 300

NUM_COL_CODES = [
    "NOJNAI", "NOKMAI", "NOSMAI",
    "BCDFHS", "BCNOHS", "EWNOHS",
    "OPDFHS", "OPNOHS", "OPPHHS",
    "SCDFHS", "SCNOHS", "STNOHS",
    "EWNOOS",
    "OPDFOS", "OPNOOS", "OPPHOS",
    "SCDFOS", "SCNOOS",
    "STNOOS", "STPHOS",
]


def code_to_schema(code: str):
    base = {
        "NOJNAI": ("AI", "OPEN", "Jain Minority"),
        "NOKMAI": ("AI", "OPEN", "Kashmiri Migrant"),
        "NOSMAI": ("AI", "OPEN", "Sikh Minority"),
        "BCDFHS": ("HS", "OBC-NCL", "Defence"),
        "BCNOHS": ("HS", "OBC-NCL", ""),
        "EWNOHS": ("HS", "EWS", ""),
        "OPDFHS": ("HS", "OPEN", "Defence"),
        "OPNOHS": ("HS", "OPEN", ""),
        "OPPHHS": ("HS", "OPEN (PwD)", ""),
        "SCDFHS": ("HS", "SC", "Defence"),
        "SCNOHS": ("HS", "SC", ""),
        "STNOHS": ("HS", "ST", ""),
        "EWNOOS": ("OS", "EWS", ""),
        "OPDFOS": ("OS", "OPEN", "Defence"),
        "OPNOOS": ("OS", "OPEN", ""),
        "OPPHOS": ("OS", "OPEN (PwD)", ""),
        "SCDFOS": ("OS", "SC", "Defence"),
        "SCNOOS": ("OS", "SC", ""),
        "STNOOS": ("OS", "ST", ""),
        "STPHOS": ("OS", "ST (PwD)", ""),
    }
    quota, seat, note = base[code]
    return quota, seat, "Gender-Neutral", note


def render_pages():
    WORK.mkdir(parents=True, exist_ok=True)
    raw_dir = WORK / "raw"
    rot_dir = WORK / "rot"
    raw_dir.mkdir(exist_ok=True)
    rot_dir.mkdir(exist_ok=True)
    if not list(raw_dir.glob("p-*.png")):
        print(f"Rendering PDF at {DPI} DPI...", flush=True)
        subprocess.check_call(["pdftoppm", "-png", "-r", str(DPI), str(PDF), str(raw_dir / "p")])
    for p in raw_dir.glob("p-*.png"):
        out = rot_dir / p.name
        if out.exists():
            continue
        Image.open(p).rotate(90, expand=True).save(out)
    return sorted(rot_dir.glob("p-*.png"))


def detect_grid(img_path: Path):
    img = cv2.imread(str(img_path))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, bw = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
    H, W = bw.shape

    vert = cv2.morphologyEx(bw, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, 100)))
    col_idx = np.where(vert.sum(axis=0) / 255 > H * 0.15)[0]
    horz = cv2.morphologyEx(bw, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (200, 1)))
    row_idx = np.where(horz.sum(axis=1) / 255 > W * 0.12)[0]

    def cluster(arr, gap):
        out = []
        if len(arr) == 0:
            return out
        cur = [int(arr[0])]
        for v in arr[1:]:
            if int(v) - cur[-1] <= gap:
                cur.append(int(v))
            else:
                out.append(int(round(np.mean(cur))))
                cur = [int(v)]
        out.append(int(round(np.mean(cur))))
        return out

    # Vertical (columns): tight gap — column lines are sharp & distinct.
    # Horizontal (rows): looser gap (40 px) — there's a faint shadow line a few
    # dozen pixels above each real row boundary; merge them.
    return cluster(col_idx, gap=8), cluster(row_idx, gap=40), img


def normalize_columns(col_xs):
    """Drop the leftmost line if it's a sub-50px artifact, ensure 24 boundaries."""
    while len(col_xs) > 25 and col_xs[1] - col_xs[0] < 50:
        col_xs = col_xs[1:]
    return col_xs


def normalize_rows(row_ys):
    """No-op — the gap=40 cluster in detect_grid already deduplicates near-line pairs."""
    return list(row_ys)


def assign_cells(words_df, col_xs, row_ys):
    """Bucket every OCR'd word into its (row_idx, col_idx) cell. Returns dict[(r,c)] = list of words."""
    buckets = {}
    for _, w in words_df.iterrows():
        try:
            cx = int(w["left"]) + int(w["width"]) // 2
            cy = int(w["top"]) + int(w["height"]) // 2
        except (ValueError, TypeError):
            continue
        # Find column
        c_idx = None
        for i in range(len(col_xs) - 1):
            if col_xs[i] <= cx < col_xs[i + 1]:
                c_idx = i
                break
        if c_idx is None:
            continue
        # Find row
        r_idx = None
        for i in range(len(row_ys) - 1):
            if row_ys[i] <= cy < row_ys[i + 1]:
                r_idx = i
                break
        if r_idx is None:
            continue
        buckets.setdefault((r_idx, c_idx), []).append((cy, int(w["left"]), str(w["text"])))
    return buckets


def cell_text(buckets, r, c, sep=" "):
    """Reconstruct cell text in correct reading order:
        1. group words into lines by y-coordinate (within ~18 px)
        2. sort each line by x-coordinate
        3. join lines top-to-bottom
    """
    words = buckets.get((r, c), [])
    if not words:
        return ""
    words = sorted(words, key=lambda w: w[0])  # sort by y first
    lines = []
    cur_y, cur_line = None, []  # cur_line: list of (x, text)
    for y, x, t in words:
        if cur_y is None or abs(y - cur_y) <= 18:
            cur_line.append((x, t))
            cur_y = y if cur_y is None else (cur_y + y) // 2
        else:
            cur_line.sort(key=lambda p: p[0])
            lines.append(" ".join(tt for _, tt in cur_line))
            cur_line = [(x, t)]
            cur_y = y
    if cur_line:
        cur_line.sort(key=lambda p: p[0])
        lines.append(" ".join(tt for _, tt in cur_line))
    return sep.join(lines)


_RE_NUM = re.compile(r"\b(\d{4,7})\b")
_RE_MIN = re.compile(r"min[^\d]{0,8}(\d{4,7})", re.I)
_RE_MAX = re.compile(r"max[^\d]{0,8}(\d{4,7})", re.I)


def parse_open_close(text: str):
    if not text:
        return None, None
    open_m = _RE_MIN.search(text)
    close_m = _RE_MAX.search(text)
    open_r = int(open_m.group(1)) if open_m else None
    close_r = int(close_m.group(1)) if close_m else None
    if open_r is None and close_r is None:
        # Sometimes labels missing — fallback to first two numbers in order
        nums = _RE_NUM.findall(text)
        if len(nums) >= 2:
            open_r, close_r = int(nums[0]), int(nums[1])
        elif len(nums) == 1:
            open_r = close_r = int(nums[0])
    return open_r, close_r


def extract_page(img_path: Path, page_num: int):
    col_xs, row_ys, img = detect_grid(img_path)
    col_xs = normalize_columns(col_xs)
    row_ys = normalize_rows(row_ys)
    if len(col_xs) < 24 or len(row_ys) < 4:
        print(f"  [WARN] {img_path.name}: insufficient grid ({len(col_xs)} cols, {len(row_ys)} rows)")
        return []

    print(f"  {img_path.name}: {len(col_xs)} col-lines, {len(row_ys)} row-lines · OCR…", flush=True)
    pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    df = pytesseract.image_to_data(pil, output_type=pytesseract.Output.DATAFRAME, config="--psm 6")
    df = df.dropna(subset=["text"])
    df = df[df["text"].astype(str).str.strip() != ""]
    print(f"    {len(df)} words", flush=True)

    buckets = assign_cells(df, col_xs, row_ys)

    # Skip header row(s). Header band is short (~70 px); data rows ≥80 px.
    records = []
    n_data_rows = len(row_ys) - 1
    for r in range(0, n_data_rows):
        # Header / title slivers
        if row_ys[r + 1] - row_ys[r] < 80:
            continue
        inst = cell_text(buckets, r, 1).replace(" | ", " ")
        course = cell_text(buckets, r, 2).replace(" | ", " ")
        inst = re.sub(r"\s+", " ", inst).strip(" ,;|")
        course = re.sub(r"\s+", " ", course).strip(" ,;|")
        if not inst or len(inst) < 6:
            continue
        for c_idx, code in enumerate(NUM_COL_CODES):
            cell = cell_text(buckets, r, 3 + c_idx)
            open_r, close_r = parse_open_close(cell)
            if open_r is None and close_r is None:
                continue
            quota, seat, gender, note = code_to_schema(code)
            records.append({
                "Page": page_num,
                "Institute": inst,
                "Program": course,
                "Quota": quota,
                "Seat": seat,
                "Gender": gender,
                "Note": note,
                "Code": code,
                "Opening Rank (int)": open_r,
                "Closing Rank (int)": close_r,
            })
    return records


def clean_institute(name: str) -> str:
    """Strip OCR artefacts: leading SI.No digits, common spelling errors."""
    s = name.strip()
    s = re.sub(r"^[\W\d]+", "", s)            # leading non-letters
    s = re.sub(r"\s+", " ", s)
    s = s.replace("Dethi", "Delhi").replace("Dethi-", "Delhi-")
    s = s.replace("Sirfort", "Sirifort")
    # Normalise PIN format (e.g., "Delhi-110085")
    s = s.strip(" ,;|")
    return s


def clean_program(name: str) -> str:
    s = re.sub(r"\s+", " ", name).strip(" ,;|")
    s = s.replace("Engineerin ", "Engineering ").replace("Engineerin,", "Engineering,")
    if s.endswith("Engineerin"):
        s = s + "g"
    return s


def main():
    pages = render_pages()
    print(f"Pages: {len(pages)}", flush=True)
    all_records = []
    for i, p in enumerate(pages, 1):
        recs = extract_page(p, i)
        print(f"    -> {len(recs):,} cells with cutoffs", flush=True)
        all_records.extend(recs)

    df = pd.DataFrame(all_records)
    if df.empty:
        print("No records extracted. Check grid detection / OCR config.")
        return

    df_out = df.drop(columns=["Page"]).copy()

    # Clean institute / program text
    df_out["Institute"] = df_out["Institute"].astype(str).map(clean_institute)
    df_out["Program"] = df_out["Program"].astype(str).map(clean_program)

    # Drop rows where the institute name is too short (OCR garbage)
    df_out = df_out[df_out["Institute"].str.len() >= 8].reset_index(drop=True)
    # Drop rows where the program name is too short
    df_out = df_out[df_out["Program"].str.len() >= 3].reset_index(drop=True)

    # Fix half-rows by mirroring
    df_out["Opening Rank (int)"] = df_out["Opening Rank (int)"].fillna(df_out["Closing Rank (int)"]).astype("Int64")
    df_out["Closing Rank (int)"] = df_out["Closing Rank (int)"].fillna(df_out["Opening Rank (int)"]).astype("Int64")
    # Drop implausible ranks
    df_out = df_out[(df_out["Opening Rank (int)"] >= 1) & (df_out["Closing Rank (int)"] <= 2_000_000)].reset_index(drop=True)
    # Ensure open <= close
    swap = df_out["Opening Rank (int)"] > df_out["Closing Rank (int)"]
    df_out.loc[swap, ["Opening Rank (int)", "Closing Rank (int)"]] = df_out.loc[swap, ["Closing Rank (int)", "Opening Rank (int)"]].values

    df_out.to_csv(OUT_CSV, index=False)
    print(f"\nWrote {OUT_CSV} ({len(df_out):,} rows)")
    print(f"  unique institutes: {df_out['Institute'].nunique()}")
    print(f"  unique programs:   {df_out['Program'].nunique()}")
    print(f"  per-quota: {df_out.groupby('Quota').size().to_dict()}")
    print(f"  per-seat:  {df_out.groupby('Seat').size().to_dict()}")
    print("\nSample:")
    print(df_out.head(5).to_string())


if __name__ == "__main__":
    main()
