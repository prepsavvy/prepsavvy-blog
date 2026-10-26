# The philosophy doctorate decision: SED 2025 evidence

Prepared **26 October 2026** for the planned **27 October 2026 edition**. The data source is the **2025 Survey of Earned Doctorates**, release **NSF 26-326**, published **25 September 2026**. The reference period is **1 July 2024 to 30 June 2025**. The edition label does not claim data were retrieved or an article published on 27 October.

## Three field scopes

| Scope | What is available | What it does not establish |
|---|---|---|
| Detailed Philosophy: SED-CIP `38.01, 38.99` | 413 doctorates awarded in 2025; Table 3-1, mapped by Table A-4 | Philosophy-only time, funding, debt or employment rates |
| Philosophy and religious studies, SED-CIP major `38` | Combined-field time, tuition-remission and graduation-plan profiles | An outcome for Philosophy alone |
| Humanities | Primary financial support and education-related debt | Philosophy-specific borrowing or a program's funding offer |

The combined major has 628 recipients: Philosophy 413, Religion/religious studies 128, and the remaining philosophy/religious-studies category 87. Humanities has 3,355 recipients. The public cells retain these labels; they are never joined as one interchangeable population. SED's detailed Philosophy mapping also differs from the `38.01` Scorecard bachelor's scope in the separate outcomes study.

## Exact populations and missing information

- **Time:** Median 6.8 years from defined doctoral start, 9.5 from graduate-school start and 11 since the bachelor's degree, for the combined major. Defined doctoral start can include master's entry at the same doctoral institution in the same field or a prerequisite master's. These are alternative starting points, not durations to add together. Exact time-item response counts are not printed and remain null.
- **Tuition remission:** The combined profile reports 91.5%. Questionnaire A7 includes full **or partial** remission. It is not a living stipend, proof of full funding or funding duration. The exact item-response denominator is not printed and remains null rather than being assigned the whole 628-person field universe.
- **Primary support:** Humanities has 2,898 respondents. A38/A39 asks about educational and living expenses across all graduate degrees, including master's and doctorate. Primary means the source supplying the greatest total support. Teaching assistantships are 41.4%, fellowships/scholarships/dissertation grants 35.6%, own resources 18.2%, research assistantships/traineeships 1.9% and employer/other 3.0%. Rounded shares total 100.1%.
- **Graduate debt:** Humanities has 2,926 respondents; 1,982 report none and 944 positive debt. The published $35,000 median applies only to the positive-debt group. A40 asks about education-related money owed at doctorate receipt, using amount brackets. It is not Scorecard's federal-only loan-disbursement measure, and graduate debt can include master's education. Do not call $35,000 the median for all graduates.
- **Plans:** 538 combined-field recipients report status, while 90 of the 628 do not. The published shares among reporters are employment 40.0%, postdoctoral training 21.6%, seeking employment/study 33.8% and other 4.6%. Unreported status is not unemployment. Employment includes returning to or continuing predoctoral employment, so these data are not a first-job placement probability.
- **Employment sectors:** Academe 72.6%, government 2.8%, industry/business 7.9%, nonprofit 11.6% and other/unknown 5.1% concern definite employment respondents. Their exact global employment denominator is not printed in the selected percentage table; no integer count is reconstructed from rounded shares. Academe does not mean tenure-track work.

Table 6-1 independently reports 331 definite commitments in the combined field: 289 U.S., 41 abroad and one unknown location. U.S. counts reconcile as 96 postdoctoral study + 142 academic employment + 15 industry + 36 other/unknown = 289. Do not use the U.S.-only sector counts as the denominator for global employment percentages.

The survey describes people who received research doctorates, including nonrespondents whose core graduation facts can be recovered from administrative sources. It does not include an entering-student population or those who left without a doctorate. No applicant completion probability, job probability, school ranking or causal PhD ROI is calculated. Professional doctorates are outside the survey's research-doctorate target population.

## Frozen source cells

`cells.json` and `cells.csv` contain **453 selected source-native cells** from seven official tables, not individual respondent data. Every cell retains its official table, worksheet, coordinate, row/column context, field, subgroup, raw value, unit and source URL. Eight selected cells are suppressed and remain `D` with a null numeric value. `-` separately means not calculable. Neither is zero-filled.

`definitions.json` records the definitions used above. `manifest.json` pins data files and all 18 official acquisition artifacts by SHA-256, byte size, URL and retrieval timestamp. The artifacts are the seven workbooks, seven matching table PDFs, survey description, questionnaire, survey root page and cycle page. No raw HTML, local cache path, credentials or private archive URI is published.

The selected source tables are [A-4](https://ncses.nsf.gov/pubs/nsf26326/assets/technical-tables/tables/nsf26326-taba-004.xlsx), [3-1](https://ncses.nsf.gov/pubs/nsf26326/assets/data-tables/tables/nsf26326-tab003-001.xlsx), [8-15](https://ncses.nsf.gov/pubs/nsf26326/assets/data-tables/tables/nsf26326-tab008-015.xlsx), [9-15](https://ncses.nsf.gov/pubs/nsf26326/assets/data-tables/tables/nsf26326-tab009-015.xlsx), [6-1](https://ncses.nsf.gov/pubs/nsf26326/assets/data-tables/tables/nsf26326-tab006-001.xlsx), [4-1](https://ncses.nsf.gov/pubs/nsf26326/assets/data-tables/tables/nsf26326-tab004-001.xlsx) and [4-4](https://ncses.nsf.gov/pubs/nsf26326/assets/data-tables/tables/nsf26326-tab004-004.xlsx). Definition footnotes are in their corresponding PDFs, linked in the manifest, and the [questionnaire](https://ncses.nsf.gov/1979/assets/0/files/earned-doctorates-2025.pdf).

## Reproduce without infrastructure

From the repository root, Python's standard library reproduces the field totals, time, support, debt, status and destination summaries from the frozen cells:

```shell
python -S scripts/doctorate_decision.py --no-charts
python -m unittest discover -s tests -p 'test_doctorate_decision.py' -v
```

`chart-inputs.json` is written under `figures/philosophy-doctorates/2026-10-27/`. Matplotlib is optional and only needed for the two branded PNG/SVG charts:

```shell
python scripts/doctorate_decision.py
```

For a full source-cell replay, download the seven linked XLSX files outside this repository, keeping their original filenames. The calculator checks each original workbook's pinned hash and reads its OpenXML using only the standard library. A content-addressed directory using hash filenames also works:

```shell
python -S scripts/doctorate_decision.py --no-charts --raw-cache-dir /absolute/path/to/official-workbooks
```

All 453 selected cells were replayed against original workbooks. An independent reviewer also downloaded fresh official workbooks and verified their hashes, source cells and questionnaire/table definitions. Public reproduction does not rely on a private repository, API key, warehouse or live API.
