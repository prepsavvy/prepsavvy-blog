# Test-optional scholarship tiers, fall 2027

This separate study freezes **16 alternative eligibility routes across nine published tiers at two U.S. public universities**. It does not extend or replace the earlier three-school Alabama snapshot. The planned edition label is 27 October 2026; all three original official pages were acquired on 26 October 2026.

## Bounded scope

* **University of Kentucky:** nonresident Bluegrass academic award only. Four annual tiers, with four no-test GPA routes and three alternative ACT/SAT pairs, create ten normalized rows. Competitive, resident and special-program awards are excluded.
* **Eastern Kentucky University:** ordinary on-campus Kentucky-resident first-time freshman merit grid. Five named awards, with ACT/SAT alternatives for Regent's, create six normalized rows. Special-program GPA exceptions, older start years, transfer and out-of-state awards are excluded.

The UKY minimum-threshold routes overlap. The calculator takes the highest qualifying published tier for each academic-condition example, including no-test alternatives where stated. **It does not add awards, determine complete eligibility or predict offered aid.** EKU's greater-value institutional rule likewise prevents adding its President's and Regent's awards. EKU at ACT 27 uses the no-test President's baseline, not a scored 27-point award.

The chart's UKY unweighted GPA 3.50 and EKU GPA 3.80 examples describe different residency populations. Neither chart measures net price, college generosity or the expected return from retaking a test. All amounts are annual published figures. No four-year cash total is computed.

## Files and reproduction

`merit.json` retains numeric ranges, evidence text, deadline/renewal/stacking conditions, source references and explicit unknowns. `merit.csv` is a tabular export; structured fields are JSON strings. `manifest.json` contains SHA-256 checksums, official source URLs, byte counts and acquisition times. No raw HTML, credentials, private warehouse identifiers or local paths are exported.

From the repository root, Python 3.10+ calculation and tests require only the standard library:

```sh
python scripts/test_optional_scholarships.py
python -m unittest discover -s tests -p test_test_optional_scholarships.py -v
```

The calculation writes `figures/test-optional-scholarships/2026-10-27/chart-inputs.json`. To reproduce both branded charts:

```sh
python -m pip install matplotlib
python scripts/test_optional_scholarships.py --render
```

Charts use the repository's shared `scripts/chart_theme.py`, Manrope fonts and PrepSavvy logo. Frozen checksums fail closed on changed input. Live application decisions require checking the current university sources.

## Source and policy boundaries

1. [UKY fall-2027 incoming freshman page](https://studentsuccess.uky.edu/financial-aid-and-scholarships/academic-scholarships/incoming-freshmen-scholarships): current grid, no ACT/SAT superscores, limited funds, December 1, 2026 application/supporting-documents deadline and encouraged May 1, 2027 acceptance. The page explicitly calls Bluegrass four-year renewable: minimum 12 undergraduate hours each semester and 3.0 cumulative GPA. Outside-award stacking, ordinary weekday cutoff time and current-cycle citizenship criteria remain unresolved. An older FAQ identifying itself as 2026-27 is not used to fill these fields.
2. [EKU current scholarship grid](https://www.eku.edu/scholarship-Opportunities/): explicit 2026-27 and 2027-28 heading, current five award rows and renewal rows. The older 2025-26 table on the same page is excluded. Regent's and President's renewal GPA is 3.2; the other awards require 3.0. All list 24 earned EKU hours/full-time enrollment. Promise also requires a learning contract.
3. [EKU linked merit policy](https://www.eku.edu/in/guides/scholarships-merit-scholarship-policies-guidelines/): undated general terms, linked by the current grid. Eight continuous semesters; minimum 12 hours each term; FAFSA; no ACT superscore; greater-value institutional award instead of stacking. All historical start-year tables are excluded. A wholly online program or more than 24 credits from another institution cancels new-freshman eligibility under the linked terms. Outside aid must be reported and total aid is subject to cost of attendance.

EKU's SAT superscore treatment, citizenship restriction and the assessment period for 24 earned hours are not explicitly supplied by accepted sources. FAFSA is **not** converted into a citizen-only rule. Admission March 1, acceptance June 1 and upgrade June 30 are stored as month/day because the relevant deadline sentences do not print calendar years or cutoff timezones. Published GPA hundredth-point bands are preserved without invented rounding. EKU awards remain subject to funds.
