# Philosophy bachelor's earnings and federal debt

Prepared on **26 October 2026** for the planned **27 October 2026 edition**, using the U.S. Department of Education's **15 October 2026** College Scorecard release. The directory date is an edition label, not an invented retrieval or publication date. Source retrieval timestamps and checksums are in `manifest.json`.

## Scope and coverage

The source filter is four-digit CIP `3801` (Philosophy) and credential level `3` (Bachelor's Degree). It excludes religion `3802`, other subject groups and graduate credentials. The four-digit group can contain several six-digit philosophy classifications; this is not a table limited to general philosophy `38.0101` or professional philosophers.

The file contains 819 matching institution rows, reduced to **802 OPEID6/CIP4/credential groups**. Twenty-six foreign-control groups are retained for audit with `domestic_scope=false`. Domestic comparisons use the other **776 non-foreign groups**, corresponding to 793 source rows. These are program-group records in this release, not a census of currently operating departments.

Debt and earnings are calculated at OPEID6 level and repeated across linked campuses. The calculator counts each pooled group once and keeps every branch name and source UNITID. Names explicitly identify pooled groups. Foreign institutions can have `NA` UNITIDs; these placeholders are not shared numeric campus identities.

| Domestic disclosure coverage | Groups |
|---|---:|
| Four-year earnings reported | 81 |
| Four-year earnings privacy-suppressed | 692 |
| Four-year earnings unavailable | 3 |
| Student federal debt median reported | 72 |
| Both four-year earnings and debt medians reported | 50 |
| Four-year earnings count at least 30 | 26 |
| Public groups meeting that display floor | 22 |

The count floor of 30 is an editorial comparison rule, not an asserted IRS suppression threshold. Missing earnings do not rank a program last. `PS` and `NA` remain distinct statuses with null numeric values; neither is replaced by zero.

## Why these six UC groups

The comparison includes **every non-foreign University of California group** in this source with disclosed four-year earnings and at least 30 disclosed earnings observations. Debt availability is not an inclusion condition. Nine UC groups appear in the source; Berkeley, Davis, Los Angeles, Riverside, Santa Barbara and Santa Cruz qualify. Irvine, San Diego and Merced have privacy-suppressed four-year earnings and earnings counts and are therefore omitted. This selection and all three omitted records are reproduced in `uc_scope` in the calculator output.

## Definitions and cohorts

| Measure | Completion cohort | Measurement and dollars |
|---|---|---|
| Four-year earnings, `EARN_MDN_4YR` | AY2017–18 and AY2018–19 | CY2022 and CY2023, adjusted to 2024 dollars |
| Four-year earnings count, `EARN_COUNT_WNE_4YR` | Same four-year earnings cohort | Count of measured completers |
| Student federal debt, `DEBT_ALL_STGP_ANY_MDN` and `_N` | AY2022–23 and AY2023–24 | Median loan disbursements and borrower count, as reported |
| One-year earnings | AY2020–21 and AY2021–22 | CY2022 and CY2023, adjusted to 2024 dollars |
| Five-year earnings | AY2016–17 and AY2017–18 | CY2022 and CY2023, adjusted to 2024 dollars |
| Seven-year earnings | AY2014–15 and AY2015–16 | CY2022 and CY2023, adjusted to 2024 dollars |

`dictionary.json` preserves the official definition and exact cohort string for each retained metric. Earnings cover federally aided completers who worked and were not enrolled during the measurement year, subject to the technical documentation's exclusions, including deceased individuals. Graduates may have obtained another credential before measurement. This is not a highest-degree-remained-bachelor's population, occupational salary scale or philosophy PhD salary comparison.

The national four-year benchmark is **$54,455**, with **$34,926** and **$78,043** quartiles and **6,085** measured workers. These values come directly from the repeated national fields. They are not averages of disclosed school medians and are never summed across institution rows. The publisher's geographic population is retained; no domestic-only interpretation of its national benchmark is asserted.

The student debt measure covers federal Stafford/Direct and Grad PLUS loan disbursements under the `ANY` institution basis. For this undergraduate credential it describes student federal borrowing and excludes private loans and Parent PLUS. It is not the degree's price or a current outstanding balance. Debt and earnings concern different completing classes and populations; no causal return, debt-payback period or matched-graduate ROI is calculated. One-, four-, five- and seven-year earnings columns also describe different cohorts and cannot be plotted as these individuals' longitudinal pay growth.

Earnings medians and counts receive privacy noise. Fine rank differences should not be treated as precise causal distinctions. `EARN_COUNT_HIGH_CRED_*` fields are excluded because the current four-year higher-credential count has an older cohort than current four-year earnings; no higher-credential share is computed. The October 2026 graduate-inclusion erratum states program-level calculations were unaffected. The older entry-cohort alignment erratum also exempts field-of-study post-completion earnings.

## Files and reproduction

- `programs.json` contains the normalized source groups, raw metric tokens, numeric values and statuses.
- `programs.csv` contains the same data with separate numeric, raw and status columns. Branch lists are JSON-encoded cells.
- `dictionary.json` contains retained metric definitions and cohort strings.
- `manifest.json` pins these files and all seven official acquisition artifacts by SHA-256, with source URLs, sizes and retrieval timestamps. It contains no credentials, local paths or raw HTML.
- `../../../figures/philosophy-outcomes/2026-10-27/chart-inputs.json` is calculated from these records and contains coverage, national benchmarks, program comparisons and UC inclusion/exclusion evidence.

Run from the repository root. The calculator and tests require only Python's standard library; `-S` verifies that no installed packages are loaded:

```shell
python -S scripts/philosophy_outcomes.py --no-charts
python -m unittest discover -s tests -p 'test_philosophy_outcomes.py' -v
```

For the branded PNG/SVG charts, install Matplotlib and run:

```shell
python scripts/philosophy_outcomes.py
```

To verify every retained outcome against original source bytes, download the [official October 15 ZIP](https://ed-public-download.scorecard.network/downloads/Most-Recent-Cohorts-Field-of-Study_10152026.zip) outside this repository. The calculator checks its pinned SHA-256 and replays all 802 groups and 819 source rows without a network request:

```shell
python -S scripts/philosophy_outcomes.py --no-charts --raw-zip /absolute/path/to/Most-Recent-Cohorts-Field-of-Study_10152026.zip
```

The source ZIP hash is `d42cd9ec5ffb4868e0f87f988fdbe10dc6c78adf427f9f6e5026a706d715be06`. Other official sources, including the [dictionary](https://collegescorecard.ed.gov/files/CollegeScorecardDataDictionary.xlsx), [technical documentation](https://collegescorecard.ed.gov/files/FieldOfStudyDataDocumentation.pdf) and both errata, are pinned in the manifest. The complete raw download remains upstream; this public edition contains normalized factual institutional data rather than individual student records.
