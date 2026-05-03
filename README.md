# College Predictor — JoSAA + CSAB 2025

A single-page, offline JEE counselling predictor merging **JoSAA Round 6 (final)** and **CSAB Special Round 3** cutoffs for NITs, IIITs, and GFTIs.

**Live:** https://sethihardik45.github.io/college-predictor/

## What it does

Enter a category rank and the tool surfaces every NIT / IIIT / GFTI seat where the rank stands a real chance — across both counsellings, in one ranked list. 12,164 cutoff rows total.

- **Bandwidth search**: starts at ±10% around your rank and expands until it finds at least N options
- **Quota gating**: HS / OS / AI / GO / JK / LA auto-applied against home state
- **Filters**: institute type, source round, quota, institute, free-text program search
- **Exports**: CSV, Excel (.xls), or print-to-PDF, all stamped with student profile

## How it's built

```
scrape_josaa.py      → josaa_2025_r6_*.csv     (8,829 rows)
scrape_csab.py       → csab_2025_final_*.csv   (3,335 rows)
build_unified.py     → index.html              (12,164 rows, self-contained)
```

The two scrapers walk the ASP.NET dropdown postback chain on `josaa.admissions.nic.in` and `admissions.nic.in/csabspl/`. The builder normalizes CSAB's verbose quota names (`Home State` → `HS`, etc.) to JoSAA codes so a single filter works across both.

`index.html` is one self-contained file with all data, CSS, and JS inlined — no build step, no server, no API calls.

## Run locally

```bash
open index.html        # macOS
xdg-open index.html    # Linux
```

To regenerate from the raw CSVs:

```bash
python3 -m venv .venv
.venv/bin/pip install pandas openpyxl
.venv/bin/python build_unified.py
```

## Disclaimer

Cutoff data is for the 2025 admission cycle and reflects each round's final state at scrape time. Always cross-check with the official JoSAA / CSAB portals before locking choices.

## Sources

- JoSAA: https://josaa.admissions.nic.in
- CSAB: https://admissions.nic.in/csabspl/
