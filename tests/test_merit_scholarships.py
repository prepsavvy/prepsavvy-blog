import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import merit_scholarships as study


class MeritChartTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle, cls.manifest = study.load_bundle()

    def test_exact_three_threshold_claims(self):
        results = [study.panel_data(self.bundle['offers'], panel) for panel in study.PANELS]
        self.assertEqual([(r['before'], r['after'], r['increase']) for r in results], [(15000, 24000, 9000), (17500, 22500, 5000), (8500, 10000, 1500)])

    def test_gpa_condition_changes_the_applicable_uab_award(self):
        lower = study.matched_band(self.bundle['offers'], 'uab', 32, 3.4)
        higher = study.matched_band(self.bundle['offers'], 'uab', 32, 3.75)
        self.assertEqual(study.annual_cash(lower), 17500)
        self.assertEqual(study.annual_cash(higher), 22500)

    def test_unmatched_is_not_zero_dollars(self):
        with self.assertRaises(LookupError):
            study.matched_band(self.bundle['offers'], 'ua', 20, 3.75)
        points = study.panel_data(self.bundle['offers'], study.PANELS[0])['steps']
        self.assertIsNone(points[0]['annual_cash_usd'])

    def test_duplicated_band_is_ambiguous(self):
        rows = copy.deepcopy(self.bundle['offers'])
        row = study.matched_band(rows, 'uab', 32, 3.75)
        rows.append(copy.deepcopy(row))
        with self.assertRaises(study.AmbiguousBandsError):
            study.matched_band(rows, 'uab', 32, 3.75)

    def test_ua_tuition_upgrade_does_not_silently_become_cash(self):
        with self.assertRaises(study.AmbiguousBandsError):
            study.matched_band(self.bundle['offers'], 'ua', 36, 4.0)
        elite = next(row for row in self.bundle['offers'] if row['award_kind'] == 'tuition_plus')
        with self.assertRaises(ValueError):
            study.annual_cash(elite)

    def test_considered_range_is_not_its_maximum(self):
        optional = study.matched_band(self.bundle['offers'], 'uab', None, 3.75, exam='NONE')
        self.assertEqual(optional['award_kind'], 'cash_range')
        with self.assertRaises(ValueError):
            study.annual_cash(optional)

    def test_una_housing_is_not_added_to_cash_or_extended_to_four_years(self):
        award = study.matched_band(self.bundle['offers'], 'una', 30, 3.75)
        self.assertEqual(study.annual_cash(award), 10000)
        self.assertEqual(award['housing']['annual_usd'], 4000)
        self.assertEqual(award['housing']['years'], 2)

    def test_input_hash_change_stops_reproduction(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            for filename in ['manifest.json', 'merit.json', 'merit.csv']:
                (target / filename).write_bytes((study.DEFAULT_DATA / filename).read_bytes())
            with (target / 'merit.json').open('a') as handle:
                handle.write(' ')
            with self.assertRaisesRegex(ValueError, 'checksum'):
                study.load_bundle(target)


if __name__ == '__main__':
    unittest.main()
