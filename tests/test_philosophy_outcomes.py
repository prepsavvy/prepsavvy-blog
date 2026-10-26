import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/philosophy_outcomes.py'
spec = importlib.util.spec_from_file_location('outcomes', SCRIPT)
outcomes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(outcomes)


class OutcomesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records, cls.manifest = outcomes.load()
        cls.summary = outcomes.calculate(cls.records)

    def test_frozen_coverage_reconciles(self):
        s = self.summary
        self.assertEqual((s['source_groups'], s['source_unitid_rows']), (802, 819))
        self.assertEqual((s['domestic_groups'], s['domestic_unitid_rows'], s['foreign_audit_groups']), (776, 793, 26))
        self.assertEqual(s['coverage']['EARN_MDN_4YR'], {'privacy_suppressed': 692, 'reported': 81, 'not_available': 3})
        self.assertEqual(s['both_earnings_and_debt'], 50)
        self.assertEqual(len(s['comparison']), 26)
        self.assertEqual(s['public_comparison_count'], 22)

    def test_national_distribution_is_publisher_benchmark(self):
        n = self.summary['national_benchmark']
        self.assertEqual([n[k] for k in ['EARN_P25_4YR_NAT', 'EARN_MDN_4YR_NAT', 'EARN_P75_4YR_NAT', 'EARN_COUNT_WNE_4YR_NAT']], [34926, 54455, 78043, 6085])

    def test_uc_all_values_and_sample_counts(self):
        expected = {'001312': (63326,67,12891,80), '001313': (58633,38,16216,46),
                    '001315': (61754,104,11337,84), '001316': (51402,47,15944,49),
                    '001320': (71796,73,11599,68), '001321': (51398,46,15178,34)}
        self.assertEqual(len(self.summary['uc_comparison']), 6)
        for r in self.summary['uc_comparison']:
            self.assertEqual((r['earnings'],r['earnings_n'],r['debt']['value'],r['debt_n']['value']), expected[r['opeid6']])
            self.assertFalse(r['pooled'])

    def test_uc_selection_covers_all_eligible_campuses(self):
        s = self.summary['uc_scope']
        self.assertEqual((s['source_uc_groups'], s['included']), (9, 6))
        self.assertEqual({r['opeid6'] for r in s['omitted']}, {'001314', '001317', '041271'})
        self.assertTrue(all(r['earnings']['status'] == 'privacy_suppressed' and r['earnings_n']['status'] == 'privacy_suppressed' for r in s['omitted']))
        changed = copy.deepcopy(self.records)
        next(r for r in changed if r['opeid6'] == '001312')['measures']['DEBT_ALL_STGP_ANY_MDN'] = outcomes.decoded('PS')
        self.assertEqual(len(outcomes.calculate(changed)['uc_comparison']), 6)

    def test_missing_is_never_zero_filled(self):
        for raw in ['PS', 'NA', 'NULL', '']:
            self.assertIsNone(outcomes.decoded(raw)['value'])
        self.assertEqual(outcomes.decoded('0')['value'], 0)
        self.assertNotEqual(outcomes.decoded('PS')['status'], outcomes.decoded('NA')['status'])

    def test_tampered_raw_numeric_value_fails(self):
        bad = copy.deepcopy(self.records)
        bad[0]['measures']['EARN_MDN_4YR']['value'] = 0
        with self.assertRaises(ValueError):
            outcomes.validate(bad)

    def test_foreign_filter_cannot_be_toggled(self):
        bad = copy.deepcopy(self.records)
        next(r for r in bad if r['control'] == 'Foreign')['domestic_scope'] = True
        with self.assertRaisesRegex(ValueError, 'Domestic scope'):
            outcomes.validate(bad)

    def test_branch_groups_not_counted_as_independent_campuses(self):
        r = next(r for r in self.records if r['opeid6'] == '002629')
        self.assertEqual(len(r['unitids']), 3)
        self.assertTrue(r['pooled_branch_group'])
        self.assertIn('pooled', r['display_name'])
        self.assertEqual(sum(x['opeid6'] == '002629' for x in self.summary['comparison']), 1)

    def test_duplicate_program_rejected(self):
        with self.assertRaisesRegex(ValueError, 'duplicated'):
            outcomes.validate(self.records + [self.records[0]])

    def test_conflicting_national_benchmark_rejected(self):
        bad = copy.deepcopy(self.records)
        row = next(r for r in bad if r['national']['EARN_MDN_4YR_NAT']['status'] == 'reported')
        row['national']['EARN_MDN_4YR_NAT'] = outcomes.decoded('99999')
        with self.assertRaisesRegex(ValueError, 'national benchmark'):
            outcomes.calculate(bad)

    def test_official_zip_hash_checked_before_replay(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'wrong.zip'
            p.write_bytes(b'not the official source')
            with self.assertRaisesRegex(ValueError, 'ZIP hash'):
                outcomes.raw_replay(p, self.records, self.manifest)

    def test_edition_file_hash_checked(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for name in ['manifest.json', *self.manifest['files']]:
                shutil.copyfile(outcomes.DATA/name, root/name)
            (root/'programs.json').write_text('[]')
            with self.assertRaisesRegex(ValueError, 'checksum'):
                outcomes.load(root)

    def test_release_date_does_not_invent_acquisition_date(self):
        self.assertEqual(self.manifest['planned_edition'], '2026-10-27')
        self.assertEqual(self.manifest['source_release'], '2026-10-15')
        self.assertEqual({x['retrieved_at'][:10] for x in self.manifest['source_files']}, {'2026-10-26'})


if __name__ == '__main__':
    unittest.main()
