import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from humanities_growth import calculate


def row(year, unit, cip, awards):
    return dict(year=year, unitid=unit, cipcode=cip, awards=awards,
                institution=unit, state='CA', city='City', control='1', sector='1')


class HumanitiesCalculationTest(unittest.TestCase):
    def test_national_population_and_matched_comparison_are_distinct(self):
        rows = [row(2021,'A','99',200), row(2021,'A','23.0101',100),
                row(2024,'A','99',400), row(2024,'A','23.0101',150),
                row(2024,'B','99',200), row(2024,'B','23.0101',50)]
        result = calculate(rows, [2021,2024])
        self.assertEqual(result['national'][1]['humanities_awards'],200)
        self.assertEqual(len(result['institutions']),1)
        a = result['public_growth'][0]
        self.assertEqual(a['change_pct'],50)
        self.assertEqual(a['share_change_pp'],-12.5)

    def test_missing_detailed_row_means_no_awards_only_with_total(self):
        rows = [row(2021,'A','99',100),row(2021,'A','23.0101',25),row(2024,'A','99',100)]
        self.assertEqual(calculate(rows,[2021,2024])['institutions'][0]['change_awards'],-25)
        with self.assertRaises(ValueError):
            calculate(rows+[row(2024,'B','23.0101',1)],[2021,2024])

    def test_rejects_duplicates_aggregates_and_overcounts(self):
        base = [row(2021,'A','99',100),row(2024,'A','99',100)]
        for extra in [[base[0]], [row(2021,'A','23',20)], [row(2021,'A','23.0101',101)]]:
            with self.assertRaises(ValueError):
                calculate(base+extra,[2021,2024])


if __name__ == '__main__':
    unittest.main()
