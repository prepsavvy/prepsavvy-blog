"""Method tests that run without private infrastructure or network access."""
import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('department_studies', Path(__file__).resolve().parents[1] / 'scripts' / 'department_studies.py')
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)


def configuration():
    return {'publication_years': '2015-2024', 'growth_windows': [[2015, 2019], [2020, 2024]],
        'candidate_journals': [{'source_id': 'journal'}]}


def works():
    rows = []
    for year in range(2015, 2025):
        for n in range(10):
            rows.append({'id': f'{year}-{n}', 'doi': f'https://doi.org/test/{year}/{n}',
                'publication_year': year, 'cited_by_count': n,
                'primary_location': {'source': {'id': 'journal'}},
                'authorships': [{'institutions': [
                    {'id': 'A', 'display_name': 'University A', 'country_code': 'US', 'type': 'education'},
                    {'id': 'B', 'display_name': 'University B', 'country_code': 'GB', 'type': 'education'}]}]})
    return rows


class PublicDepartmentMethodTests(unittest.TestCase):
    def test_unknown_source_is_rejected(self):
        data = works()
        data[0]['primary_location']['source']['id'] = 'unknown'
        with self.assertRaisesRegex(ValueError, 'outside configured source'):
            engine.calculate(data, configuration(), minimum=1)

    def test_absent_configured_journal_is_rejected(self):
        config = configuration()
        config['candidate_journals'].append({'source_id': 'missing'})
        with self.assertRaisesRegex(ValueError, 'Configured journal is missing'):
            engine.calculate(works(), config, minimum=1)

    def test_raw_acknowledgment_branch_records_hash_and_withholds_credit(self):
        previous = engine.AFFILIATION_RULES
        engine.AFFILIATION_RULES = {'reject_pattern': 'seminar participants', 'aliases': {}, 'overrides': {}}
        try:
            data = works()[:1]
            data[0]['authorships'][0]['raw_affiliation_strings'] = ['seminar participants at University A and University B']
            reviewed, audit = engine.review_affiliations(data)
            self.assertEqual(reviewed[0]['authorships'][0]['institutions'], [])
            self.assertEqual(len(audit[0]['raw_affiliation_sha256']), 64)
        finally:
            engine.AFFILIATION_RULES = previous

    def test_shared_credit_conserves_publication_and_decile_mass(self):
        rows, _, _, _ = engine.calculate(works(), configuration(), minimum=1)
        self.assertEqual(sum(r['fractional_articles'] for r in rows), 100)
        self.assertEqual(sum(r['top_decile_equivalent'] for r in rows), 10)
        self.assertEqual([r['rank'] for r in rows], [1, 1])

    def test_zero_citation_boundary_ties_are_fractional(self):
        data = works()
        for row in data:
            row['cited_by_count'] = 0
        rows, _, _, _ = engine.calculate(data, configuration(), minimum=1)
        self.assertAlmostEqual(sum(r['top_decile_equivalent'] for r in rows), 10)

    def test_duplicate_doi_blocks_ranking(self):
        data = works()
        data[0]['doi'] = data[1]['doi']
        with self.assertRaisesRegex(ValueError, 'Duplicate DOI'):
            engine.calculate(data, configuration(), minimum=1)

    def test_missing_publication_year_blocks_ranking(self):
        with self.assertRaisesRegex(ValueError, 'Incomplete publication years'):
            engine.calculate(works()[:-10], configuration(), minimum=1)

    def test_growth_reports_counts_separately_from_rate(self):
        rows, _, _, _ = engine.calculate(works(), configuration(), minimum=1)
        self.assertEqual(rows[0]['articles_early'], 50)
        self.assertEqual(rows[0]['articles_recent'], 50)
        self.assertEqual(rows[0]['output_change'], 0)
        self.assertEqual(rows[0]['output_change_pct'], 0)


if __name__ == '__main__':
    unittest.main()
