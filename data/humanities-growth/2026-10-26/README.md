# Humanities degree growth: 2021 to 2024

Evidence edition built 26 October 2026. The accompanying article is a draft, not a published ranking of department quality. The records are a reproducible extract of public NCES IPEDS data collected 22 October 2026, not a new scrape of 2026 graduates.

## Reproduce without credentials

From the repository root, with Python 3.11 or newer:

```sh
python scripts/humanities_growth.py --data data/humanities-growth/2026-10-26 --output analysis/humanities-growth/2026-10-26
python -m unittest discover -s tests -v
python -m pip install -r requirements.txt
python scripts/humanities_graphs.py --data data/humanities-growth/2026-10-26 --output figures/humanities-growth/2026-10-26
```

The calculator verifies every input hash, row count and national total before writing the comparison tables. The chart renderer independently recalculates those records. Original chart design uses the bundled Manrope font, PrepSavvy brand blue, green for growth and the supplied wordmark.

## Definition

- Geography: the 50 U.S. states and District of Columbia; other territories are excluded.
- Population: first-major bachelor awards, IPEDS award level 5, in 2020–21 and 2023–24. Awards can include both BA and BS degrees. They are not unduplicated people, enrollment, faculty positions or current program capacity.
- Included detailed CIP codes: `16.xxxx` languages/linguistics; `23.xxxx` English/writing; `38.xxxx` philosophy/religious studies; `54.xxxx` history; `24.0103` humanities/humanistic studies.
- Excluded: broad liberal/general studies, arts, communications and area studies. This is narrower than some other organizations' humanities definitions.
- National totals use each year's reporting institutions. Campus changes require the same UNITID in both years. No name-based mergers or system aggregation.
- Public growth table: institutions classified public in both years with at least 100 included awards in 2021; order by absolute increase. Equal increases share a displayed rank. The threshold selects 186 institutions, not every public college.
- A missing detailed subject record contributes no awards only when that institution's reported bachelor's total exists. A missing institution/year is never treated as zero.
- Reporting flags are retained (`R`, reported; the source also contains one `C` flag). Detailed source records, not rounded chart labels, determine calculations.

## Files and provenance

`program-awards.csv` contains 21,954 rows: institution bachelor totals (`CIP 99`) and the selected detailed subject records, with institution names, UNITIDs, geography and source reporting flags. `manifest.json` records the exact source snapshot, upstream archive URLs/checksums, export timestamp, SQL hash and data hash. `warehouse-query.sql` preserves the executed query template and parameters are declared in the manifest. It is unnecessary for public reproduction because all calculation records are included.

The private acquisition/export module is `research/humanities_growth.py` in `prepsavvy/intelligence`; the public calculation and chart code are in this repository. Original upstream ZIP archives can be downloaded using the URLs in the manifest, without accessing the PrepSavvy warehouse. The manifest identifies one immutable complete, non-quarantined source snapshot.

The national counts reconcile to 87,916 and 75,626 humanities awards, and 2,069,260 and 1,959,325 total bachelor awards. Subject subtotals reconcile to institution totals. The independent calculator checks duplicate keys, out-of-scope aggregate codes, missing totals and impossible counts. Tests cover changing institution populations and the distinction between award growth and share growth.

## Interpretation and limitations

Two observations do not establish continuous growth. The baseline is pandemic-affected. Changes may reflect cohort timing, classification changes, mergers or institutional reporting, as well as changes in student interest or program resources. The primary case studies use stable UNITIDs and show the detailed subject movements; they do not attribute causes. Public history is included with history so a transfer between those codes cannot alone create the combined increase. Annual cohorts and department reporting should be checked before making claims about sustained program expansion.

Official current catalogs establish that the programs named in the article exist. They do not establish why awards changed. The article sources and raw subject breakdown are included separately. No university has endorsed these findings.

NCES data remain attributed to their federal source. PrepSavvy's original compilation and figures are CC BY 4.0; original code is MIT licensed. Cite PrepSavvy, *Humanities degree growth: 2021 to 2024*, data edition 2026-10-26, with a link to this directory.
