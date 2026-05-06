"""Extract JAC Delhi 2025 Round-5 cutoffs from the 4 PDFs.

JAC Delhi (Joint Admission Counselling) coordinates B.Tech admissions to:
  • DTU      (Delhi Technological University)
  • NSUT     (Netaji Subhas University of Technology)
  • IGDTUW   (Indira Gandhi Delhi Technical University for Women)
  • IIIT Delhi  — uses its own "IIIT Rank" scale derived from JEE Main +
                 board-marks bonus, NOT directly comparable with JEE Main
                 CRL. We deliberately exclude it from the unified predictor.

Category code grammar (5 chars):
    [CC][SS][D|O]
        CC : GN=General · EW=EWS · OB=OBC-NCL · SC=SC · ST=ST
        SS : GN=Gender-Neutral · GL=Girl(female) · SG=Single-Girl
             CW=Children-of-War (Defence) · PD=PwD
        D|O: D=Delhi (Home State) · O=Outside Delhi

Plus standalone "KM" = Kashmiri Migrant (treated as AI quota).

Each cutoff is the LAST RANK ALLOTTED (closing rank) on JEE-Main 2025 CRL.
JAC publishes only one rank per (branch × category) — so opening = closing.
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import pdfplumber

ROOT = Path(__file__).parent
JAC_DIR = ROOT / "JAC"
OUT_CSV = ROOT / "jac_2025_final.csv"

# All 4 institutes are in Delhi (HS quota = Delhi domicile)
INSTITUTES = {
    "DTU":    "Delhi Technological University, Bawana Road, Delhi-110042",
    "NSUT":   "Netaji Subhas University of Technology, Sector-3, Dwarka, New Delhi-110078",
    "IGDTUW": "Indira Gandhi Delhi Technical University for Women, Kashmere Gate, Delhi-110006",
}


def code_to_schema(code: str):
    """Map a JAC category code → (quota, seat, gender, note).
    Returns None for codes we should skip.
    """
    if code == "KM":
        return ("AI", "OPEN", "Gender-Neutral", "Kashmiri Migrant")
    if code == "SG":
        # Single Girl is a Delhi-residing female reserved seat
        return ("HS", "OPEN", "Female-only (including Supernumerary)", "Single Girl")
    m = re.match(r"^([A-Z]{2})([A-Z]{2})([DO])$", code)
    if not m:
        return None
    cc, ss, ds = m.groups()
    quota = "HS" if ds == "D" else "OS"
    seat_base = {"GN": "OPEN", "EW": "EWS", "OB": "OBC-NCL", "SC": "SC", "ST": "ST"}.get(cc)
    if seat_base is None:
        return None
    seat = f"{seat_base} (PwD)" if ss == "PD" else seat_base
    if ss == "GL" or ss == "SG":
        gender = "Female-only (including Supernumerary)"
    else:
        gender = "Gender-Neutral"
    note = ""
    if ss == "CW":
        note = "Defence"
    elif ss == "SG":
        note = "Single Girl"
    elif code == "GNKM":
        note = "Kashmiri Migrant"
    return (quota, seat, gender, note)


_PHASE_RE = re.compile(r"\([^)]*\)")
_NUM_RE = re.compile(r"^\d{2,7}$")


def strip_phase(token: str) -> str:
    """Remove "(IV)" / "(V(v))" / "(VI)" suffix from a rank value token."""
    return _PHASE_RE.sub("", token).strip()


def cluster_by_top(words, gap=4):
    """Group words into row-bands by their `top` y-coordinate."""
    if not words:
        return []
    words = sorted(words, key=lambda w: (w["top"], w["x0"]))
    bands = []
    cur = [words[0]]
    cur_top = words[0]["top"]
    for w in words[1:]:
        if abs(w["top"] - cur_top) <= gap:
            cur.append(w)
            cur_top = (cur_top + w["top"]) / 2
        else:
            bands.append(sorted(cur, key=lambda x: x["x0"]))
            cur = [w]
            cur_top = w["top"]
    bands.append(sorted(cur, key=lambda x: x["x0"]))
    return bands


def find_header_row(bands, expected_codes):
    """Find a band that contains at least 2 of the expected category codes."""
    for band in bands:
        texts = [w["text"] for w in band]
        hits = sum(1 for code in expected_codes if code in texts)
        if hits >= 2:
            return band
    return None


def assign_to_columns(values, col_xs, tolerance=30):
    """Map a list of (x, value) tuples to column indices by nearest x."""
    out = [None] * len(col_xs)
    for x, v in values:
        # Find closest column x
        best_i, best_d = None, 1e9
        for i, cx in enumerate(col_xs):
            d = abs(cx - x)
            if d < best_d:
                best_d = d
                best_i = i
        if best_i is not None and best_d <= tolerance:
            if out[best_i] is None:    # don't overwrite
                out[best_i] = v
    return out


# ──────────────────── DTU ────────────────────
DTU_DELHI_COLS = ["GNGND","GNGLD","EWGND","EWGLD","OBGND","OBGLD","SCGND","SCGLD",
                  "STGND","STGLD","GNSGD","GNPDD","EWPDD","OBPDD","SCPDD","STPDD"]
DTU_DELHI_CW_COLS = ["GNCWD","EWCWD","OBCWD","SCCWD","STCWD"]
DTU_OUTSIDE_COLS = ["GNGNO","GNGLO","EWGNO","EWGLO","OBGNO","OBGLO","SCGNO","SCGLO",
                    "STGNO","STGLO","GNPDO","EWPDO","OBPDO","SCPDO"]
DTU_OUTSIDE_CW_COLS = ["GNCWO","EWCWO","OBCWO","SCCWO","STCWO"]


SUBTITLE_TOKENS = {"Defense", "Defence", "(CW)", "(KM)", "Kashmiri", "Migrants", "(KM)–", "–", "—"}


def _dtu_parse_table(words, header_codes, y_top, y_bottom):
    """Parse one DTU sub-table bounded by (y_top, y_bottom).

    Each logical row is anchored on its S.No. (a 1-2 digit at x<100). Values
    sit on the same y-line as the S.No.; the Branch may sit on the same line
    OR wrap upward to one line above (DTU lays out long branch names with the
    1st line above the S.No. and the 2nd line beside the S.No.).
    """
    in_range = [w for w in words if y_top <= w["top"] <= y_bottom]
    if not in_range:
        return []
    bands = cluster_by_top(in_range, gap=3)
    hdr = find_header_row(bands, header_codes)
    if not hdr:
        return []
    col_x_pairs = []
    for code in header_codes:
        w = next((x for x in hdr if x["text"] == code), None)
        if w:
            col_x_pairs.append((w["x0"], (w["x0"] + w["x1"]) / 2, code))
    col_x_pairs.sort(key=lambda p: p[0])
    if not col_x_pairs:
        return []
    col_xs = [(c, code) for _, c, code in col_x_pairs]
    branch_x_max = col_x_pairs[0][0] - 8    # branch column ends just before first value column
    val_x_min = col_x_pairs[0][0] - 12
    header_bot = max(w["top"] for w in hdr)

    # All S.No. anchors (small ints at x<100, below the header)
    snos = sorted(
        [w for w in in_range
         if w["x0"] < 100 and w["text"].isdigit() and len(w["text"]) <= 2 and w["top"] > header_bot + 5],
        key=lambda w: w["top"],
    )

    out = []
    for i, sno in enumerate(snos):
        sno_y = sno["top"]
        prev_y = header_bot if i == 0 else snos[i - 1]["top"]
        # Branch words: 100 ≤ x < branch_x_max, y in (prev_y + 4, sno_y + 4]
        branch_words = sorted(
            [w for w in in_range
             if prev_y + 4 < w["top"] <= sno_y + 4
             and 100 <= w["x0"] < branch_x_max
             and not re.match(r"^\d+$", w["text"])
             and w["text"] not in SUBTITLE_TOKENS],
            key=lambda w: (w["top"], w["x0"]),
        )
        branch = re.sub(r"\s+", " ", " ".join(w["text"] for w in branch_words)).strip(" ,;|")
        if not branch or len(branch) < 4:
            continue

        # Values: same y as S.No. (within ±5), at x ≥ val_x_min
        value_words = [w for w in in_range
                       if abs(w["top"] - sno_y) <= 5
                       and w["x0"] >= val_x_min
                       and re.match(r"^\d+", w["text"])]
        vals = []
        for w in value_words:
            txt = strip_phase(w["text"]).replace(",", "")
            if txt.isdigit():
                cx = (w["x0"] + w["x1"]) / 2
                vals.append((cx, int(txt)))
        aligned = assign_to_columns(vals, [x for x, _ in col_xs], tolerance=30)
        for j, v in enumerate(aligned):
            if v is None:
                continue
            out.append((branch, col_xs[j][1], v))
    return out


def parse_dtu(pdf_path: Path):
    """DTU has 2 sub-tables per page: Main + CW. We split them by y-range
    determined from the header positions.
    """
    records = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            main_cols = DTU_DELHI_COLS if page_num == 0 else DTU_OUTSIDE_COLS
            cw_cols = DTU_DELHI_CW_COLS if page_num == 0 else DTU_OUTSIDE_CW_COLS
            words = page.extract_words()
            # Locate header y-positions
            main_y = next((w["top"] for w in words if w["text"] == main_cols[0]), None)
            cw_y = next((w["top"] for w in words if w["text"] == cw_cols[0]), None)
            if main_y is None:
                continue
            page_bottom = max(w["top"] for w in words)

            if cw_y is not None and cw_y > main_y:
                # Main table runs from main_y to a few px above cw_y
                records.extend(_dtu_parse_table(words, main_cols, main_y - 5, cw_y - 20))
                records.extend(_dtu_parse_table(words, cw_cols, cw_y - 5, page_bottom))
            else:
                records.extend(_dtu_parse_table(words, main_cols, main_y - 5, page_bottom))
    return records


# ──────────────────── NSUT ────────────────────
NSUT_DELHI_COLS = ["GNGND","GNGLD","EWGND","EWGLD","OBGND","OBGLD","SCGND","SCGLD",
                   "STGND","STGLD","GNCWD","EWCWD","OBCWD","SCCWD","STCWD",
                   "GNPDD","EWPDD","OBPDD","SCPDD","STPDD","KM"]
NSUT_OUTSIDE_COLS = ["GNGNO","GNGLO","EWGNO","EWGLO","OBGNO","OBGLO","SCGNO","SCGLO",
                     "STGNO","STGLO","GNCWO","EWCWO","OBCWO","SCCWO","STCWO",
                     "GNPDO","EWPDO","OBPDO","SCPDO","STPDO"]


def parse_nsut(pdf_path: Path):
    """NSUT layout: a single wide row per branch on each of pages 1 & 2.
    Branch code (e.g. "CSAI", "CSE") is the leftmost non-numeric word.
    Values may have phase suffixes "(IV)" / "(V(v))" / "(VI)" etc.
    """
    records = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            cols = NSUT_DELHI_COLS if page_num == 0 else NSUT_OUTSIDE_COLS
            words = page.extract_words()
            bands = cluster_by_top(words, gap=4)
            hdr = find_header_row(bands, cols)
            if not hdr:
                continue
            col_xs = []
            for code in cols:
                w = next((x for x in hdr if x["text"] == code), None)
                if w:
                    col_xs.append(((w["x0"] + w["x1"]) / 2, code))
            col_xs.sort(key=lambda p: p[0])

            # Data rows: bands whose leftmost word is a short alphanumeric (CSE, CSAI, …)
            # and that contain at least 4 numeric values.
            for band in bands:
                if not band:
                    continue
                first = band[0]
                # Branch labels are short alphabetic codes ending optionally with *
                if not re.match(r"^[A-Z]{2,7}\*?$", first["text"]):
                    continue
                # Reject the Course-Code key on page bottom
                if first["text"] in {"Code", "Cod", "Course"}:
                    continue
                # Need to count numeric values
                num_vals = [w for w in band if re.match(r"^\d", w["text"])]
                if len(num_vals) < 4:
                    continue
                # NSUT may have multi-token entries like "457248 (VIII)" — pdfplumber
                # may split them. Re-merge: find numeric words, check if next word
                # is a "(...)" parenthetical at similar y.
                branch = first["text"]
                merged = []
                for i, w in enumerate(num_vals):
                    merged.append(w)
                vals = []
                for w in merged:
                    txt = strip_phase(w["text"])
                    if txt.isdigit():
                        cx = (w["x0"] + w["x1"]) / 2
                        vals.append((cx, int(txt)))
                aligned = assign_to_columns(vals, [x for x, _ in col_xs], tolerance=35)
                for i, v in enumerate(aligned):
                    if v is None:
                        continue
                    records.append((branch, col_xs[i][1], v))
    return records


# Map NSUT branch codes → full names (from the legend on each page)
NSUT_BRANCH_NAMES = {
    "CSAI": "Computer Science and Engineering (Artificial Intelligence)",
    "CSE":  "Computer Science and Engineering",
    "CSDS": "Computer Science and Engineering (Data Science)",
    "IT":   "Information Technology",
    "ITNS": "Information Technology and Network Security",
    "MAC":  "Mathematics and Computing",
    "ECE":  "Electronics and Communication Engineering",
    "EVDT": "Electronics Engineering (VLSI Design and Technology)",
    "EE":   "Electrical Engineering",
    "ICE":  "Instrumentation and Control Engineering",
    "ME":   "Mechanical Engineering",
    "MPAE": "Manufacturing Process and Automation Engineering",
    "BT":   "Biotechnology",
    "CSDA": "Computer Science and Engineering (Big Data Analytics)",
    "CIOT": "Computer Science and Engineering (Internet of Things)",
    "ECAM": "Electronics and Communication Engineering (Advanced Communication Technology)",
    "ECIOT":"Electronics and Communication Engineering (IoT)",
    "GTAR": "Geo-informatics",
    "BAE":  "B.Arch",
    "MSME": "MSME",
    "BBA":  "BBA",
}


# ──────────────────── IGDTUW ────────────────────
IGDTUW_BRANCH_HDR = ["CSE-AI","CSE","ECE-AI","ECE","IT","AIML","MAE","DMAM","MAC","B.Arch"]


def parse_igdtuw(pdf_path: Path):
    """IGDTUW layout: branches as columns, categories as rows. Skip B.Arch (Paper 2).
    Page 1 = Delhi; page 2 = Outside.
    """
    records = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            outside = (page_num == 1)
            words = page.extract_words()
            bands = cluster_by_top(words, gap=4)

            # Header band: contains "CSE-AI" "CSE" "ECE-AI" etc.
            hdr = None
            for band in bands:
                texts = [w["text"] for w in band]
                if all(b in texts for b in ["CSE-AI", "CSE", "ECE-AI", "IT"]):
                    hdr = band
                    break
            if not hdr:
                continue
            # Get x-positions for each branch (skip B.Arch)
            col_xs = []
            for branch in IGDTUW_BRANCH_HDR:
                w = next((x for x in hdr if x["text"] == branch), None)
                if w and branch != "B.Arch":
                    col_xs.append(((w["x0"] + w["x1"]) / 2, branch))

            # Data rows: leftmost word matches a category code
            # Some codes like "GNCWD", "GNGND", etc.
            for band in bands:
                if not band:
                    continue
                first = band[0]
                code = first["text"]
                # Allow 5-char codes + "SG" + "KM"
                if not (re.match(r"^[A-Z]{2,5}$", code) or code in ("SG", "KM")):
                    continue
                if code in {"Code", "Category"}:
                    continue
                # On the Outside page (O suffix), shift codes accordingly. The PDF
                # lists category codes already with the right suffix on each page.
                vals = []
                for w in band[1:]:
                    txt = strip_phase(w["text"])
                    if txt.replace(",", "").isdigit():
                        cx = (w["x0"] + w["x1"]) / 2
                        vals.append((cx, int(txt.replace(",", ""))))
                if len(vals) < 1:
                    continue
                aligned = assign_to_columns(vals, [x for x, _ in col_xs], tolerance=30)
                for i, v in enumerate(aligned):
                    if v is None:
                        continue
                    records.append((col_xs[i][1], code, v))
    return records


def main():
    # ---- DTU ----
    dtu = parse_dtu(JAC_DIR / "2025071619.pdf")
    print(f"DTU: {len(dtu):,} cells")

    # ---- NSUT ----
    nsut = parse_nsut(JAC_DIR / "2025071627.pdf")
    print(f"NSUT: {len(nsut):,} cells")

    # ---- IGDTUW ----
    igdtuw = parse_igdtuw(JAC_DIR / "2025071699.pdf")
    print(f"IGDTUW: {len(igdtuw):,} cells")

    rows = []
    # DTU records: (branch, code, rank)
    for branch, code, rank in dtu:
        sch = code_to_schema(code)
        if sch is None:
            continue
        quota, seat, gender, note = sch
        rows.append({
            "Institute": INSTITUTES["DTU"],
            "Program": branch,
            "Quota": quota, "Seat": seat, "Gender": gender, "Note": note,
            "Code": code,
            "Opening Rank (int)": rank,
            "Closing Rank (int)": rank,
        })
    for branch_code, code, rank in nsut:
        prog = NSUT_BRANCH_NAMES.get(branch_code.rstrip("*"), branch_code)
        sch = code_to_schema(code)
        if sch is None:
            continue
        quota, seat, gender, note = sch
        rows.append({
            "Institute": INSTITUTES["NSUT"],
            "Program": prog,
            "Quota": quota, "Seat": seat, "Gender": gender, "Note": note,
            "Code": code,
            "Opening Rank (int)": rank,
            "Closing Rank (int)": rank,
        })
    igdtuw_branch_names = {
        "CSE":    "Computer Science and Engineering",
        "CSE-AI": "Computer Science and Engineering (Artificial Intelligence)",
        "ECE":    "Electronics and Communication Engineering",
        "ECE-AI": "Electronics and Communication Engineering (Artificial Intelligence)",
        "IT":     "Information Technology",
        "AIML":   "Artificial Intelligence and Machine Learning",
        "MAE":    "Mechanical and Automation Engineering",
        "MAC":    "Mathematics and Computing",
        "DMAM":   "Digital Media and Multimedia Engineering",
    }
    for branch, code, rank in igdtuw:
        sch = code_to_schema(code)
        if sch is None:
            continue
        quota, seat, gender, note = sch
        # IGDTUW is women-only — force Female-only gender for all rows
        gender = "Female-only (including Supernumerary)"
        prog = igdtuw_branch_names.get(branch, branch)
        rows.append({
            "Institute": INSTITUTES["IGDTUW"],
            "Program": prog,
            "Quota": quota, "Seat": seat, "Gender": gender, "Note": note,
            "Code": code,
            "Opening Rank (int)": rank,
            "Closing Rank (int)": rank,
        })

    df = pd.DataFrame(rows)
    if df.empty:
        print("No records extracted!")
        return
    # Drop implausible ranks
    df = df[(df["Closing Rank (int)"] >= 1) & (df["Closing Rank (int)"] <= 2_000_000)]
    df.to_csv(OUT_CSV, index=False)
    print(f"\nWrote {OUT_CSV} ({len(df):,} rows)")
    print(f"  by institute: {df.groupby('Institute').size().to_dict()}")
    print(f"  unique programs: {df['Program'].nunique()}")
    print(f"  by quota: {df.groupby('Quota').size().to_dict()}")
    print(f"  by seat:  {df.groupby('Seat').size().to_dict()}")
    print(f"  by gender:{df.groupby('Gender').size().to_dict()}")
    print(f"  notes:    {sorted(df['Note'].unique())}")
    print("\nSample DTU rows:")
    print(df[df['Institute'].str.contains('DTU')].head(5).to_string())


if __name__ == "__main__":
    main()
