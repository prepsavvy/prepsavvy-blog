# PrepSavvy economics research index, edition 2026-10-27

Data and code behind [The Best Economics Schools in the World, Ranked by Research](https://prepsavvy.ai/blog/best-economics-schools-in-the-world).

## Reproduce the ranking

```
python calculate.py
```

The script uses Python's standard library only. It recalculates every university's score from `works.jsonl`, writes `reproduced-index.csv`, `reproduced-index.json` and `reproduced-country-shares.csv`, and checks every rank, paper count and score against `index.json` with tolerance 1e-8.

## Files

| File | Contents |
|---|---|
| `index.csv`, `index.json` | The ranking: 56 universities with at least 50 papers, with rank, research influence score, papers, citations and output change. |
| `country-shares.csv` | Each country's share of all university-attributed research influence. |
| `works.jsonl` | The 7,036 papers: OpenAlex ID, DOI, title, year, journal, citation count, authors and their institutions at publication. |
| `journals.json` | The eight journals, with ISSNs and OpenAlex source IDs. |
| `excluded-papers.json` | The 27 items removed because the publisher identifies them as prefaces, editorials, award announcements, covers or submission statistics, with the publisher page for each. |
| `calculate.py` | The calculation. |
| `manifest.json` | SHA-256 checksums of every file. |

## Method

- **Corpus:** research articles published 2015 to 2024 in the *American Economic Review*, *Econometrica*, the *Quarterly Journal of Economics*, the *Journal of Political Economy*, the *Review of Economic Studies*, the *Review of Economics and Statistics*, the *Journal of the European Economic Association* and the *Economic Journal*.
- **Top decile:** within each journal and publication year, the most-cited 10% of papers. Papers tied at the boundary share the remaining credit, so each journal-year carries exactly 10% of its papers.
- **Research influence score:** the sum of a university's top-decile credit. A paper's credit is split equally among the distinct universities on it.
- **Eligibility:** at least 50 papers. Ties are broken by fractional citations.
- **Output change:** papers in 2020 to 2024 against papers in 2015 to 2019.
- **Affiliations:** institutions at the time of publication, as indexed by OpenAlex, with credit drawn from acknowledgments removed and publisher-verified corrections applied. Only institutions typed as education receive credit.
- **Citations:** OpenAlex citation counts collected on 26 October 2026.

## Sources and license

Bibliographic metadata and citation counts come from [OpenAlex](https://openalex.org) (CC0), with journal metadata checked against Crossref. The compilation is offered under CC BY 4.0 and `calculate.py` under the MIT license. Cite it as: PrepSavvy, *Economics research index*, edition 2026-10-27, https://github.com/prepsavvy/prepsavvy-blog/tree/main/data/economics/2026-10-27.

Payment and advertising do not enter the ranking.
