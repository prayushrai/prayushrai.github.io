"""Extract UPTAC 2025 cutoffs from the saved-page HTML into a clean CSV.

UPTAC categories (OPEN, BC, SC, ST, EWS) carry sub-quota suffixes:
  (GIRL/Girl/GL) - female reservation
  (PH)           - PwD
  (TF)           - Tuition Fee Waiver
  (AF)           - Armed Forces dependent
  (FF)           - Freedom Fighter dependent

We split each row into a normalized seat type (matching JoSAA/CSAB) plus a
`note` field carrying any UPTAC-specific sub-quota tag. Only the LATEST round
per (institute, program, quota, seat, gender, note) is retained, mirroring how
JoSAA/CSAB CSVs already keep only the final round.
"""
from pathlib import Path
import re
import pandas as pd
from bs4 import BeautifulSoup

ROOT = Path(__file__).parent
SRC = ROOT / "UPTAC" / "uploads" / "Online Counselling System.html"
OUT_DIR = ROOT / "UPTAC"
OUT_CSV = OUT_DIR / "uptac_2025_final.csv"

CAT_MAP = {"OPEN": "OPEN", "BC": "OBC-NCL", "SC": "SC", "ST": "ST", "EWS": "EWS"}


def normalize_category(cat: str, seat_gender: str):
    """Return (seat, gender, note) tuple for a UPTAC category cell."""
    cat = cat.strip()
    is_pwd = "(PH)" in cat
    is_girl = "(GIRL)" in cat or "(Girl)" in cat or "(GL)" in cat
    is_af = "(AF)" in cat
    is_tf = "(TF)" in cat
    is_ff = "(FF)" in cat

    base = re.split(r"[(\s]", cat, maxsplit=1)[0]
    seat = CAT_MAP.get(base, base)
    if is_pwd:
        seat = f"{seat} (PwD)"

    if is_girl or seat_gender.strip() == "Female Seats":
        gender = "Female-only (including Supernumerary)"
    else:
        gender = "Gender-Neutral"

    note = "AF" if is_af else "TF" if is_tf else "FF" if is_ff else ""
    return seat, gender, note


QUOTA_MAP = {"Home State": "HS", "All India": "AI"}


def round_num(s: str) -> int:
    m = re.search(r"\d+", s)
    return int(m.group()) if m else 0


def main():
    soup = BeautifulSoup(SRC.read_text(errors="ignore"), "lxml")
    table = soup.find("table")
    rows = table.find_all("tr")
    headers = [c.get_text(strip=True).rstrip("▲▼") for c in rows[0].find_all(["th", "td"])]

    data = []
    for tr in rows[1:]:
        cells = [c.get_text(strip=True) for c in tr.find_all(["th", "td"])]
        if len(cells) == len(headers):
            data.append(cells)

    df = pd.DataFrame(data, columns=headers)
    print(f"Raw rows: {len(df):,}")

    df["round_num"] = df["Round"].apply(round_num)
    df["open_int"] = pd.to_numeric(df["Opening Rank"].str.replace(",", ""), errors="coerce")
    df["close_int"] = pd.to_numeric(df["Closing Rank"].str.replace(",", ""), errors="coerce")
    df = df.dropna(subset=["open_int", "close_int"]).copy()
    df["open_int"] = df["open_int"].astype(int)
    df["close_int"] = df["close_int"].astype(int)

    seat_gender_note = df.apply(
        lambda r: normalize_category(r["Category"], r["Seat Gender"]), axis=1
    )
    df["seat"] = [t[0] for t in seat_gender_note]
    df["gender"] = [t[1] for t in seat_gender_note]
    df["note"] = [t[2] for t in seat_gender_note]
    df["quota"] = df["Quota"].map(QUOTA_MAP).fillna(df["Quota"])

    # Keep latest round per unique seat combination
    df = df.sort_values("round_num").drop_duplicates(
        subset=["Institute", "Program", "quota", "seat", "gender", "note"], keep="last"
    )
    print(f"After dedupe (latest round per seat): {len(df):,}")

    final = pd.DataFrame({
        "Round": df["Round"],
        "Institute": df["Institute"].str.title(),
        "Program": df["Program"],
        "Quota": df["quota"],
        "Seat": df["seat"],
        "Gender": df["gender"],
        "Note": df["note"],
        "Opening Rank (int)": df["open_int"],
        "Closing Rank (int)": df["close_int"],
    })

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    final.to_csv(OUT_CSV, index=False)
    print(f"Wrote {OUT_CSV} ({len(final):,} rows)")
    print("\nSample:")
    print(final.head(3).to_string())


if __name__ == "__main__":
    main()
