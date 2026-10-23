# PrepSavvy research and open data

Research data and reproducible figures supporting the [PrepSavvy blog](https://prepsavvy.ai/blog).

## Philosophy research index, 23 October 2026

**Article:** [Top Philosophy Schools Worldwide for Research and Influence](https://prepsavvy.ai/blog/top-philosophy-schools). The article is an editorial draft in PrepSavvy's CMS; the public article URL will become available when it is published. Read the [article source](articles/top-philosophy-schools.md) while it is under review.

The release contains 23,457 indexed articles in 31 selected philosophy journals, a research index of 112 institutions with at least 50 articles, and U.S. philosophy-family degree awards for 2018–2024. Research measures institutional affiliations at publication. It does not measure the complete output of current department faculty or all books and languages.

| File | Contents |
|---|---|
| [schools.csv](data/2026-10-23/schools.csv) | All ranked institutions, influence, citations, publication growth and matched U.S. degree counts |
| [works.jsonl](data/2026-10-23/works.jsonl) | Frozen article identifiers, citations, journals and curated institutional affiliations |
| [program-years.csv](data/2026-10-23/program-years.csv) | Annual institution and award-level degree totals |
| [program-details.csv](data/2026-10-23/program-details.csv) | Constituent subject codes and reporting flags |
| [journals.json](data/2026-10-23/journals.json) | Explicit journal names and ISSNs |
| [affiliation-audit.json](data/2026-10-23/affiliation-audit.json) | Reviewed affiliation anomalies and retained credits |
| [manifest.json](data/2026-10-23/manifest.json) | Source URLs, collection times and data/code SHA-256 checksums |
| [sensitivity.json](data/2026-10-23/sensitivity.json) | Rankings after excluding technology journals or Synthese |

Download the [data and calculator ZIP](data/2026-10-23/philosophy-evidence.zip), or clone the repository to reproduce the figures too.

## Reproduce

Python 3.11 or newer is recommended. The calculation and integrity verification use the standard library. No credentials, API key or warehouse account are required.

```sh
python scripts/verify.py
python -m pip install -r requirements.txt
python scripts/graphs.py
```

The verifier checks every file listed in the source manifest, independently recalculates all 112 school rows, compares numeric values with tolerance 1e-8 and checks the sensitivity results. The graph script writes three figures as both PNG and SVG to `figures/2026-10-23/`. Matplotlib is pinned to 3.10.8; fonts use its bundled DejaVu Sans family.

1. **Research influence:** top 20 institutions by fractional contributions to the most-cited tenth within each journal/year.
2. **Publication growth:** selected U.S. institutions in the top 20, comparing 2015–2019 and 2020–2024 article counts.
3. **Degree trends:** bachelor's and research doctorate awards at UC Irvine, Princeton and USC, 2018–2024.

## Method and sources

Articles cover publication years 2015–2024. Citations are those indexed at collection on 23 October 2026. The influence score uses citation deciles within each journal and year; boundary ties receive fractional credit, and institutional credit is split equally across eligible education institutions. At least 50 articles are required; fractional citations break score ties. Self-citations are included. Flagged acknowledgment-like affiliation strings receive the documented review rules before institution attribution.

U.S. awards are NCES IPEDS first-major awards in detailed CIP codes within family 38.01, including philosophy, logic, ethics and related philosophy programs. Religion, clinical bioethics and joint degrees classified elsewhere are excluded. Research doctorates use award level 17. Three-year averages require all three reported years. Missing values are blank, not zero. The explicit [crosswalk](data/2026-10-23/crosswalk.json) documents campus aggregation. Rutgers bachelor's awards combine three campuses; doctorates are New Brunswick. Washington degree counts are Seattle only.

Primary sources: [OpenAlex](https://openalex.org/), [NCES IPEDS](https://nces.ed.gov/ipeds/use-the-data). Exact download/API URLs and collection hashes are in the manifest. The OpenAlex extract omits individual author identities and credentialed request parameters. The frozen, curated fields are sufficient to reproduce every published calculation; this is not a complete mirror of the upstream APIs.

## Citation and reuse

Suggested citation: PrepSavvy (2026). *Top Philosophy Schools Worldwide for Research and Influence*. Editorial draft, data edition 2026-10-23. https://prepsavvy.ai/blog/top-philosophy-schools. Supporting data and code: https://github.com/prepsavvy/prepsavvy-blog.

OpenAlex metadata are CC0. NCES federal data retain their source attribution. PrepSavvy's original compilation, prose and figures are offered under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); original reproduction code is offered under the [MIT license](LICENSE). These terms do not relicense third-party material. No academic peer review is claimed by this draft release.
