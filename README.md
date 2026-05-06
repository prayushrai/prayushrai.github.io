# PRAYUSH — JoSAA + CSAB + UPTAC + GGSIPU + JAC Delhi 2025 college predictor

A single-page, offline JEE counselling predictor unifying **JoSAA Round 6 (final)**, **CSAB Special Round 3**, **UPTAC final round**, **GGSIPU 2025 Round 3**, and **JAC Delhi 2025 Round 5** cutoffs. **18,525 cutoff rows** across NITs, IIITs, GFTIs, UPTAC institutes (AKTU), GGSIPU institutes (IPU Delhi), and JAC Delhi institutes (DTU · NSUT · IGDTUW) — one ranked list.

**Live:** https://sethihardik45.github.io/college-predictor/

## What it does

Enter a JEE Main rank and PRAYUSH surfaces every seat where the rank stands a real chance — across all five counsellings, in one ranked list.

- **Bandwidth search**: starts at ±10% around your rank and expands until it finds at least N options.
- **Quota gating**: HS / OS / AI / GO / JK / LA auto-applied against home state.
- **Sub-quotas preserved** as side tags:
  - UPTAC: PwD / AF (Armed Forces) / TF (Tuition Fee waiver) / FF (Freedom Fighter)
  - GGSIPU: Defence / Jain Minority / Kashmiri Migrant / Sikh Minority
  - JAC Delhi: Defence (CW) / Single Girl / Kashmiri Migrant
- **Filters**: institute type (NIT / IIIT / GFTI / UPTAC / GGSIPU / JAC), source round, quota, institute, free-text program search.
- **Exports**: CSV, Excel (.xls), or print-to-PDF, all stamped with student profile.

## How it's built

```
scrape_josaa.py      → josaa_2025_r6_*.csv         (8,829 rows · main JoSAA)
scrape_csab.py       → csab_2025_final_*.csv       (3,335 rows · CSAB special)
extract_uptac.py     → UPTAC/uptac_2025_final.csv  (4,926 rows · UPTAC final, deduped to latest round per seat)
extract_ggsipu.py    → ggsipu_2025_final.csv       (  663 rows · GGSIPU R3, OCR'd from scanned PDF)
extract_jac.py       → jac_2025_final.csv          (  772 rows · JAC Delhi R5: DTU + NSUT + IGDTUW)
build_unified.py     → index.html                  (18,525 rows, self-contained)
```

The JoSAA/CSAB scrapers walk the ASP.NET dropdown postback chain on the official `admissions.nic.in` portals. The UPTAC extractor parses a saved-page HTML of the AKTU online counselling system, normalizing UP-specific categories (`OPEN(GIRL)`, `BC(PH)`, `EWS(GL)`...) into the JoSAA-style `seat × gender × note` schema. The GGSIPU extractor handles a scanned image-only PDF: it renders each page at 300 DPI, detects grid lines via OpenCV morphology, runs whole-page Tesseract OCR with bounding-box mapping, then maps the 20 GGSIPU category codes (`OPDFHS`, `BCNOOS`, `NOJNAI`...) into the unified schema.

The JAC Delhi extractor parses 4 official cutoff PDFs (DTU, NSUT, IGDTUW, IIIT-Delhi) using `pdfplumber` word-position extraction. The 5-character JAC codes (`[CC][SS][D|O]`) decompose cleanly: GN/EW/OB/SC/ST × GN/GL/SG/CW/PD × Delhi/Outside. **IIIT Delhi is intentionally excluded** because it uses its own "IIIT Rank" scale (derived from JEE Main + board-marks bonus) which isn't directly comparable to JEE Main CRL.

The builder normalizes CSAB's verbose quota names (`Home State` → `HS`) to JoSAA codes so one filter spans all five counsellings.

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
