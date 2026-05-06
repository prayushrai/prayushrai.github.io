# PRAYUSH — JoSAA + CSAB + UPTAC + GGSIPU 2025 college predictor

A single-page, offline JEE counselling predictor unifying **JoSAA Round 6 (final)**, **CSAB Special Round 3**, **UPTAC final round**, and **GGSIPU 2025 Round 3** cutoffs. **17,753 cutoff rows** across NITs, IIITs, GFTIs, UPTAC institutes (AKTU), and GGSIPU institutes (IPU Delhi) — one ranked list.

**Live:** https://sethihardik45.github.io/college-predictor/

## What it does

Enter a JEE Main rank and PRAYUSH surfaces every seat where the rank stands a real chance — across all four counsellings, in one ranked list.

- **Bandwidth search**: starts at ±10% around your rank and expands until it finds at least N options.
- **Quota gating**: HS / OS / AI / GO / JK / LA auto-applied against home state.
- **Sub-quotas preserved**: UPTAC's PwD / AF (Armed Forces) / TF (Tuition Fee waiver) / FF (Freedom Fighter) and GGSIPU's Defence / Jain Minority / Kashmiri Migrant / Sikh Minority show as side tags.
- **Filters**: institute type (NIT / IIIT / GFTI / UPTAC / GGSIPU), source round, quota, institute, free-text program search.
- **Exports**: CSV, Excel (.xls), or print-to-PDF, all stamped with student profile.

## How it's built

```
scrape_josaa.py      → josaa_2025_r6_*.csv      (8,829 rows · main JoSAA)
scrape_csab.py       → csab_2025_final_*.csv    (3,335 rows · CSAB special)
extract_uptac.py     → UPTAC/uptac_2025_final.csv (4,926 rows · UPTAC final, deduped to latest round per seat)
extract_ggsipu.py    → ggsipu_2025_final.csv    (  663 rows · GGSIPU R3 OCR'd from scanned PDF)
build_unified.py     → index.html               (17,753 rows, self-contained)
```

The JoSAA/CSAB scrapers walk the ASP.NET dropdown postback chain on the official `admissions.nic.in` portals. The UPTAC extractor parses a saved-page HTML of the AKTU online counselling system, normalizing UP-specific categories (`OPEN(GIRL)`, `BC(PH)`, `EWS(GL)`...) into the JoSAA-style `seat × gender × note` schema. The GGSIPU extractor handles a scanned image-only PDF: it renders each page at 300 DPI, detects grid lines via OpenCV morphology, runs whole-page Tesseract OCR with bounding-box mapping, then maps the 20 GGSIPU category codes (`OPDFHS`, `BCNOOS`, `NOJNAI`...) into the unified schema. The builder normalizes CSAB's verbose quota names (`Home State` → `HS`) to JoSAA codes so one filter spans all four.

`index.html` is one self-contained file with all data, CSS, JS, fonts inlined — no build step, no server, no API calls.

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
