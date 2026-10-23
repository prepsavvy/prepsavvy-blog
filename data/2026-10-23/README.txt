PrepSavvy philosophy research index, edition 2026-10-23

Run python calculate.py in this directory. It uses Python's standard library only
and writes reproduced-rankings.csv, reproduced-schools.csv and sensitivity JSON.
Match institution IDs, positions and scores against schools.csv with floating
point tolerance 1e-8. The journal list is explicit.

schools.csv: worldwide institutional research index and matched U.S. award data.
program-years.csv: annual philosophy-family awards, 2018-2024, by NCES UNITID.
program-details.csv: constituent CIP codes, counts and report flags.
sensitivity.json: positions with technology journals and Synthese excluded.
crosswalk.json: curated OpenAlex-to-NCES correspondence. Rutgers aggregates three
campuses for bachelor's awards, and New Brunswick for doctorates.
Washington is explicitly Seattle-only for awards. CUNY's system entity
is not joined to its graduate-school entity. Blank means unavailable, not zero.
works.jsonl: frozen bibliographic/institution fields needed to reproduce the index.
journals.json: included journal names and ISSNs.
manifest.json: source dates and file checksums.

Research: institutional affiliations at publication; articles in the selected
English-language journal corpus, 2015-2024, citations indexed at collection.
Score: fractional contribution to the top citation decile within journal/year.
Eligibility: 50 articles. Tie-break: fractional citation total.
Degrees: first majors, CIP 38.01 detailed codes (philosophy, logic, ethics),
excluding religion, clinical bioethics and joint degrees classified elsewhere.
Three-year averages require all three reported years. Missing is never zero.
No claim that degrees awarded equal students enrolled, faculty or new intake.

OpenAlex metadata are CC0. Cite NCES releases for the federal awards data.
Attribution requested for this compilation: PrepSavvy, philosophy research index,
the dated edition. Payment and advertising do not enter the algorithm.
Human academic review must be completed and named separately;
this bundle does not assert that such review has occurred.
