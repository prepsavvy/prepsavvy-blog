import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import test_optional_scholarships as m


class ScholarshipTests(unittest.TestCase):
    def setUp(self):
        self.bundle,_ = m.load_bundle()
        self.rows = self.bundle['offers']

    def test_two_reviewed_thresholds(self):
        result = m.calculate(self.bundle)
        self.assertEqual([p['increase_annual_usd'] for p in result['panels']],[3000,2000])
        self.assertEqual((result['route_count'],result['tier_count']),(16,9))

    def test_uky_overlap_selects_highest_not_sum(self):
        routes = m.routes_at(self.rows,'uky',3.5,29,include_no_test=True)
        self.assertEqual(sorted(r['annual_amount_min'] for r in routes),[6500,10000,10000,13000])
        self.assertEqual(m.highest_tier(self.rows,'uky',3.5,29,include_no_test=True)['annual_usd'],13000)

    def test_higher_gpa_already_has_16000_without_score(self):
        self.assertEqual(m.highest_tier(self.rows,'uky',3.8,exam='NONE')['annual_usd'],16000)
        self.assertEqual(m.highest_tier(self.rows,'uky',3.8,29,include_no_test=True)['annual_usd'],16000)
        self.assertEqual(m.highest_tier(self.rows,'uky',3.8,30,include_no_test=True)['annual_usd'],16000)

    def test_eku_no_scored_award_at_27(self):
        with self.assertRaises(LookupError):
            m.highest_tier(self.rows,'eku',3.8,27)
        self.assertEqual(m.highest_tier(self.rows,'eku',3.8,27,include_no_test=True)['annual_usd'],7000)
        self.assertEqual(m.highest_tier(self.rows,'eku',3.8,28)['annual_usd'],9000)

    def test_sat_route_and_unknown_policy_remain_distinct(self):
        result = m.highest_tier(self.rows,'eku',3.8,1310,exam='SAT')
        self.assertEqual(result['annual_usd'],9000)
        row = next(r for r in self.rows if r['record_id'] in result['record_ids'])
        self.assertIsNone(row['superscore']['SAT'])
        self.assertTrue(row['fafsa_required'])
        self.assertIsNone(row['citizenship_rule'])

    def test_gpa_gap_not_rounded_into_award(self):
        with self.assertRaises(LookupError):
            m.highest_tier(self.rows,'eku',3.795,exam='NONE')
        with self.assertRaises(LookupError):
            m.highest_tier(self.rows,'uky',2.99,exam='NONE')

    def test_invalid_inputs_rejected(self):
        for score in [None,37,29.5,True]:
            with self.assertRaises(ValueError):
                m.routes_at(self.rows,'uky',3.5,score)
        with self.assertRaises(ValueError):
            m.routes_at(self.rows,'uky',4.2,30)
        with self.assertRaises(ValueError):
            m.routes_at(self.rows,'uky',3.5,30,exam='NONE')

    def test_duplicate_tier_route_wrong_cycle_and_reversed_sat(self):
        for mutation in ['duplicate','cycle','sat']:
            rows = copy.deepcopy(self.rows)
            if mutation == 'duplicate':
                rows[1] = copy.deepcopy(rows[0]);rows[1]['record_id'] = 'different-id'
            elif mutation == 'cycle':
                rows[0]['entry_year'] = 2026
            else:
                row = next(r for r in rows if r['exam']=='SAT')
                row['score_min'],row['score_max'] = 1500,1200
            with self.assertRaises(ValueError):
                m.validate_rows(rows)

    def test_manifest_tamper_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory)
            for f in ['manifest.json','merit.json','merit.csv']:
                (p/f).write_bytes((m.DEFAULT_DATA/f).read_bytes())
            (p/'merit.json').write_text('{}',encoding='utf-8')
            with self.assertRaises(ValueError):
                m.load_bundle(p)

    def test_frozen_chart_inputs_are_reproducible(self):
        expected = json.loads((m.DEFAULT_OUTPUT/'chart-inputs.json').read_text(encoding='utf-8'))
        self.assertEqual(m.calculate(self.bundle),expected)


if __name__ == '__main__':
    unittest.main()
