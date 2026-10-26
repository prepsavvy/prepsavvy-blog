import copy
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('doctorates', Path(__file__).resolve().parents[1]/'scripts/doctorate_decision.py')
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)


class DoctorateDecisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cells, cls.manifest = engine.load()
        cls.result = engine.summarize(cls.cells)

    def test_complete_cell_and_suppression_counts(self):
        self.assertEqual(len(self.cells),453)
        self.assertEqual(len({c['record_id'] for c in self.cells}),453)
        self.assertEqual(sum(c['status']=='suppressed' for c in self.cells),8)

    def test_three_scopes_are_not_conflated(self):
        s=self.result
        self.assertEqual(s['philosophy_detailed_awards']['Philosophy'],413)
        self.assertEqual(s['profiles'][engine.PHIL_REL]['field_total'],628)
        self.assertEqual(s['profiles']['Humanities']['field_total'],3355)
        self.assertNotIn('Philosophy',s['profiles'])
        self.assertEqual(s['primary_support']['field_scope'],'Humanities')

    def test_time_and_remission_do_not_invent_item_response_counts(self):
        p=self.result['profiles'][engine.PHIL_REL]
        self.assertEqual((p['years_from_defined_doctoral_start_median'],p['years_from_graduate_start_median'],p['years_since_bachelor_median']),(6.8,9.5,11))
        self.assertEqual(p['tuition_remission_percent'],91.5)
        self.assertIsNone(p['time_item_response_n'])
        self.assertIsNone(p['tuition_item_response_n'])

    def test_status_respondents_and_missing_are_separate(self):
        p=self.result['profiles'][engine.PHIL_REL]
        self.assertEqual((p['postgraduation_status_reports'],p['postgraduation_status_nonreporters']),(538,90))
        self.assertEqual(p['status_percentages'],{'postdoc_percent':21.6,'employment_percent':40,'seeking_percent':33.8,'other_percent':4.6})
        self.assertEqual(p['definite_commitments'],331)

    def test_humanities_primary_support_uses_own_respondents(self):
        f=self.result['primary_support']
        self.assertEqual(f['respondents'],2898)
        self.assertEqual(f['percentages']['Teaching assistantships'],41.4)
        self.assertEqual(f['percentages']['Fellowships, scholarships, or dissertation grants'],35.6)
        self.assertAlmostEqual(sum(f['percentages'].values()),100.1)

    def test_graduate_debt_median_is_positive_debt_subgroup(self):
        d=self.result['debt']['Graduate debt']
        self.assertEqual((d['respondents'],d['no_debt_count'],d['positive_debt_count']),(2926,1982,944))
        self.assertEqual(d['median_among_positive_debt_only_usd'],35000)
        self.assertEqual(d['no_debt_percent'],67.7)

    def test_us_destination_counts_not_global_employment_denominator(self):
        p=self.result['profiles'][engine.PHIL_REL]
        d=p['destination_counts']
        self.assertEqual((d['United States total'],d['Abroad'],d['Location unknown']),(289,41,1))
        self.assertEqual(d['United States postdoctoral study']+d['United States academic employment']+d['United States industry employment']+d['United States other sector or unknown'],289)
        self.assertEqual(p['employment_sectors_percent_of_definite_employment']['Academe'],72.6)

    def test_suppressed_cell_cannot_be_zero_filled(self):
        bad=copy.deepcopy(self.cells)
        next(c for c in bad if c['status']=='suppressed')['value']=0
        with self.assertRaisesRegex(ValueError,'suppressed'):
            engine.validate(bad)

    def test_wrong_response_denominator_stops_calculation(self):
        bad=copy.deepcopy(self.cells)
        c=next(c for c in bad if c['table']=='9-15'and c['cell']=='F5')
        c.update(raw=600,value=600)
        with self.assertRaisesRegex(ValueError,'rounded status'):
            engine.summarize(bad)

    def test_detailed_field_counts_must_reconcile(self):
        bad=copy.deepcopy(self.cells)
        c=next(c for c in bad if c['table']=='3-1'and c['cell']=='F366')
        c.update(raw=414,value=414)
        with self.assertRaisesRegex(ValueError,'Detailed fields'):
            engine.summarize(bad)

    def test_changed_official_workbook_is_rejected(self):
        source=next(s for s in self.manifest['source_files']if s['url'].endswith('.xlsx'))
        with tempfile.TemporaryDirectory()as d:
            (Path(d)/source['sha256']).write_bytes(b'wrong workbook')
            with self.assertRaisesRegex(ValueError,'checksum'):
                engine.replay_workbooks(self.cells,self.manifest,d)

    def test_frozen_file_hash_and_source_dates(self):
        self.assertEqual(self.manifest['planned_edition'],'2026-10-27')
        self.assertEqual(self.manifest['source_release'],'2026-09-25')
        self.assertEqual({a['retrieved_at'][:10]for a in self.manifest['source_files']},{'2026-10-26'})
        with tempfile.TemporaryDirectory()as d:
            for name in ['manifest.json',*self.manifest['files']]:
                shutil.copyfile(engine.DATA/name,Path(d)/name)
            (Path(d)/'cells.json').write_text('[]')
            with self.assertRaisesRegex(ValueError,'hash'):
                engine.load(d)


if __name__ == '__main__':unittest.main()
