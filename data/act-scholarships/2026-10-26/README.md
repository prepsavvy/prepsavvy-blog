# ACT scholarship tier pilot, 26 October 2026

This frozen dataset supports the draft article [ACT Scholarships for 2027: Where the Award Tiers Change](../../../articles/act-scholarship-tiers.md). It covers three selected Alabama public universities and fall 2027 entry. It is not a national scholarship directory, a representative sample or a personalized eligibility service.

`merit.json` and `merit.csv` contain **47 normalized award conditions, not 47 distinct scholarships**. ACT and SAT rows are alternative qualification routes, not amounts to add together. UAB contributes 17 conditions, Alabama 14 and North Alabama 16. There are 44 fixed-cash conditions, one considered award range and two tuition-plus routes without an invented cash valuation.

`manifest.json` supplies file hashes and the isolated warehouse snapshot reference. `merit.json` embeds five official source URLs, their acquisition timestamps and SHA-256 hashes. No raw HTML, applicant data, credentials or local cache paths are included.

## Reproduce the chart

From the repository root, using the repository's plotting dependencies:

```sh
python scripts/merit_scholarships.py
python -m unittest discover -s tests -p 'test_merit_scholarships.py'
```

The script verifies both frozen file hashes, selects each institution's ACT route at GPA 3.75 and preserves its distinct published GPA label. It writes PNG/SVG and exact plotted inputs under `figures/act-scholarships/2026-10-26/`. It performs no network requests or warehouse queries.

Unmatched scores are missing, not zero awards. Overlapping alternatives fail rather than silently choosing an award. Cash ranges and tuition packages are excluded from single-valued cash calculations. North Alabama housing remains separate, with its two-year residence-hall condition.

## Scope and unknowns

- The UAB heading says 2027–2028. Alabama and North Alabama label their grids 2027. Each heading is retained; the common normalized entry term is fall 2027.
- UAB and Alabama do not use scholarship superscores. North Alabama uses its ACT superscore based on English, Reading and Math. Do not treat the same number as identical test evidence across institutions.
- GPA weighting/conversion is not established for UAB or Alabama by these sources. North Alabama specifies unweighted GPA. Residency and citizenship conditions differ and are retained.
- UAB's selected page does not establish 2027–28 renewal duration. Alabama's standard cash-award duration is also unresolved in this source set. North Alabama has general renewal terms but does not print every award-specific continuing requirement.
- Exact deadline cutoff timezones remain unknown. Some deadline sentences omit calendar year; those full-date fields remain null rather than inferred. Read the retained source rule.
- A dated research snapshot does not guarantee an award remains available. Recheck the official current rules before applying. Annual cash amounts are not guaranteed four-year totals, net prices or a causal return from taking a test.

Official sources: [UAB](https://www.uab.edu/admissions/cost/scholarships/out-of-state-students), [Alabama award grid](https://afford.ua.edu/scholarships/oos-international-freshman/), [Alabama renewal policy](https://afford.ua.edu/scholarships/policies/), [Alabama FAQ](https://afford.ua.edu/scholarships/faq/), [North Alabama](https://www.una.edu/admissions/new-freshmen/scholarships.html).
