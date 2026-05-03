#!/usr/bin/env python3
"""Scrape JoSAA 2025 Round 6 cutoffs for NIT, IIIT, GFTI.

Fix: only send form fields for dropdowns that are actually populated
(ASP.NET EventValidation rejects values for empty dropdowns).
"""
import re
import time
import sys
import requests
from bs4 import BeautifulSoup
import pandas as pd
from pathlib import Path

URL = "https://josaa.admissions.nic.in/applicant/SeatAllotmentResult/CurrentORCR.aspx"
OUT_DIR = Path("/sessions/amazing-cool-knuth/mnt/outputs")
OUT_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://josaa.admissions.nic.in",
    "Referer": URL,
    "Cache-Control": "max-age=0",
}

HIDDEN_FIELDS = ["__VIEWSTATE", "__VIEWSTATEGENERATOR", "__EVENTVALIDATION"]


def parse_hidden(html):
    soup = BeautifulSoup(html, "lxml")
    out = {}
    for name in HIDDEN_FIELDS:
        el = soup.find("input", {"name": name})
        out[name] = el["value"] if el and el.has_attr("value") else ""
    return out, soup


def populated(soup, name):
    sel = soup.find("select", {"name": name})
    if not sel:
        return False
    opts = sel.find_all("option")
    # Consider populated if it has more than just the --Select-- option
    if len(opts) <= 1:
        return False
    return True


def build_form(hidden, event_target, values):
    """values is a dict of dropdown name -> value (only include populated ones)."""
    form = {
        "__EVENTTARGET": event_target,
        "__EVENTARGUMENT": "",
        "__LASTFOCUS": "",
        "__VIEWSTATE": hidden.get("__VIEWSTATE", ""),
        "__VIEWSTATEGENERATOR": hidden.get("__VIEWSTATEGENERATOR", ""),
        "__EVENTVALIDATION": hidden.get("__EVENTVALIDATION", ""),
        "ctl00$hdnSecKey": "",
    }
    form.update(values)
    return form


def do_post(sess, form):
    r = sess.post(URL, data=form, timeout=120, allow_redirects=True)
    r.raise_for_status()
    return r


def scrape_institute_type(instype_code, label, retry=True):
    print(f"\n=== Scraping {label} (code={instype_code}) ===", flush=True)
    sess = requests.Session()
    sess.headers.update(HEADERS)

    # Step 1: GET seed
    r = sess.get(URL, timeout=60)
    r.raise_for_status()
    hidden, soup = parse_hidden(r.text)
    time.sleep(1)

    # Step 2: select round=6 — only ddlroundno is populated
    form = build_form(hidden, "ctl00$ContentPlaceHolder1$ddlroundno",
                      {"ctl00$ContentPlaceHolder1$ddlroundno": "6"})
    r = do_post(sess, form)
    hidden, soup = parse_hidden(r.text)
    if not populated(soup, "ctl00$ContentPlaceHolder1$ddlInstype"):
        raise RuntimeError("Instype dropdown not populated after round selection")
    time.sleep(1)

    # Step 3: select instype
    form = build_form(hidden, "ctl00$ContentPlaceHolder1$ddlInstype", {
        "ctl00$ContentPlaceHolder1$ddlroundno": "6",
        "ctl00$ContentPlaceHolder1$ddlInstype": instype_code,
    })
    r = do_post(sess, form)
    hidden, soup = parse_hidden(r.text)
    if not populated(soup, "ctl00$ContentPlaceHolder1$ddlInstitute"):
        raise RuntimeError("Institute dropdown not populated after instype selection")
    time.sleep(1)

    # Step 4: select institute=ALL
    form = build_form(hidden, "ctl00$ContentPlaceHolder1$ddlInstitute", {
        "ctl00$ContentPlaceHolder1$ddlroundno": "6",
        "ctl00$ContentPlaceHolder1$ddlInstype": instype_code,
        "ctl00$ContentPlaceHolder1$ddlInstitute": "ALL",
    })
    r = do_post(sess, form)
    hidden, soup = parse_hidden(r.text)
    if not populated(soup, "ctl00$ContentPlaceHolder1$ddlBranch"):
        raise RuntimeError("Branch dropdown not populated after institute selection")
    time.sleep(1)

    # Step 5: select branch=ALL
    form = build_form(hidden, "ctl00$ContentPlaceHolder1$ddlBranch", {
        "ctl00$ContentPlaceHolder1$ddlroundno": "6",
        "ctl00$ContentPlaceHolder1$ddlInstype": instype_code,
        "ctl00$ContentPlaceHolder1$ddlInstitute": "ALL",
        "ctl00$ContentPlaceHolder1$ddlBranch": "ALL",
    })
    r = do_post(sess, form)
    hidden, soup = parse_hidden(r.text)
    if not populated(soup, "ctl00$ContentPlaceHolder1$ddlSeattype"):
        raise RuntimeError("Seattype dropdown not populated after branch selection")
    time.sleep(1)

    # Step 6: submit
    form = build_form(hidden, "", {
        "ctl00$ContentPlaceHolder1$ddlroundno": "6",
        "ctl00$ContentPlaceHolder1$ddlInstype": instype_code,
        "ctl00$ContentPlaceHolder1$ddlInstitute": "ALL",
        "ctl00$ContentPlaceHolder1$ddlBranch": "ALL",
        "ctl00$ContentPlaceHolder1$ddlSeattype": "ALL",
        "ctl00$ContentPlaceHolder1$btnSubmit": "Submit",
    })
    r = do_post(sess, form)

    soup = BeautifulSoup(r.text, "lxml")
    table = soup.find("table", {"id": "ctl00_ContentPlaceHolder1_GridView1"})
    if table is None:
        print(f"[WARN] GridView not found for {label}. Response length={len(r.text)}", flush=True)
        if retry:
            print("Retrying once with fresh session...", flush=True)
            time.sleep(3)
            return scrape_institute_type(instype_code, label, retry=False)
        return pd.DataFrame()

    rows = []
    for tr in table.find_all("tr"):
        cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
        if cells:
            rows.append(cells)

    header = ["Institute", "Academic Program Name", "Quota", "Seat Type",
              "Gender", "Opening Rank", "Closing Rank"]
    if rows and rows[0][0].lower().startswith("institute"):
        data_rows = rows[1:]
    else:
        data_rows = rows
    data_rows = [r for r in data_rows if len(r) == 7]
    df = pd.DataFrame(data_rows, columns=header)
    print(f"[{label}] parsed {len(df)} rows", flush=True)
    return df


def clean_ranks(df):
    def to_int(v):
        if not isinstance(v, str):
            return pd.NA
        m = re.match(r"^(\d+)", v.strip())
        if m:
            try:
                return int(m.group(1))
            except ValueError:
                return pd.NA
        return pd.NA
    df["Opening Rank (int)"] = df["Opening Rank"].apply(to_int).astype("Int64")
    df["Closing Rank (int)"] = df["Closing Rank"].apply(to_int).astype("Int64")
    return df


def main():
    targets = [("NIT", "nit"), ("3IT", "iiit"), ("CFI", "gfti")]
    frames = {}
    for code, slug in targets:
        try:
            df = scrape_institute_type(code, slug.upper())
        except Exception as e:
            print(f"[ERROR] {slug}: {e}", flush=True)
            df = pd.DataFrame()
        if not df.empty:
            df = clean_ranks(df)
            path = OUT_DIR / f"josaa_2025_r6_{slug}.csv"
            df.to_csv(path, index=False)
            print(f"Wrote {path} ({len(df)} rows)", flush=True)
        frames[slug] = df
        time.sleep(2)

    combined = []
    type_map = {"nit": "NIT", "iiit": "IIIT", "gfti": "GFTI"}
    for slug, df in frames.items():
        if df.empty:
            continue
        d = df.copy()
        d.insert(0, "Institute Type", type_map[slug])
        combined.append(d)

    if combined:
        all_df = pd.concat(combined, ignore_index=True)
        all_csv = OUT_DIR / "josaa_2025_r6_all.csv"
        all_df.to_csv(all_csv, index=False)
        print(f"\nWrote {all_csv} ({len(all_df)} rows)", flush=True)

        all_xlsx = OUT_DIR / "josaa_2025_r6_all.xlsx"
        with pd.ExcelWriter(all_xlsx, engine="openpyxl") as writer:
            all_df.to_excel(writer, index=False, sheet_name="R6 Cutoffs")
            ws = writer.sheets["R6 Cutoffs"]
            ws.freeze_panes = "A2"
            ncols = len(all_df.columns)
            last_col = ws.cell(row=1, column=ncols).column_letter
            ws.auto_filter.ref = f"A1:{last_col}{len(all_df)+1}"
            for i, col in enumerate(all_df.columns, start=1):
                letter = ws.cell(row=1, column=i).column_letter
                try:
                    max_len = max(len(str(col)),
                                  int(all_df[col].astype(str).str.len().max()) if len(all_df) else 10)
                except Exception:
                    max_len = 20
                ws.column_dimensions[letter].width = min(max_len + 2, 60)
        print(f"Wrote {all_xlsx}", flush=True)

        print("\nRow counts:", flush=True)
        for slug, df in frames.items():
            print(f"  {type_map[slug]}: {len(df)}", flush=True)
        print(f"  TOTAL: {len(all_df)}", flush=True)

        print("\nFirst 5 rows of combined CSV:", flush=True)
        print(all_df.head().to_string(), flush=True)
    else:
        print("[ERROR] No data scraped.", flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
