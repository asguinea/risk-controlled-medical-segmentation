"""Evidence-to-figure boundaries, independent of the rendering backend."""
import copy
from fractions import Fraction
import json
from pathlib import Path
import tempfile
import unittest

from risk_controlled_segmentation.figures import figure_data, verify_figure_data
from risk_controlled_segmentation.study import load_evidence
from risk_controlled_segmentation.riga import load_riga


class FigureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = figure_data()

    def test_locked_policy_populations_and_budget_projection(self):
        self.assertEqual(len(self.data['final']['chaksu']), 4)
        self.assertEqual(len(self.data['final']['riga']), 8)
        for row, source in zip(self.data['final']['chaksu'], load_evidence()['final']['controllers']):
            self.assertEqual(row['images'], 204)
            self.assertEqual(row['raw_omission_percent'], 100 * source['locked']['risk']['raw_average_omission'])
        for row, source in zip(self.data['final']['riga'], load_riga()['final']['policies']):
            self.assertEqual(row['images'], 182)
            self.assertEqual(row['budget_percent'], 100 * float(Fraction(source['alpha'])))
            self.assertEqual(row['origin'], source['origin'])
            self.assertEqual(row['area_percent'], 100 * source['evaluation']['spatial_utility']['region_area_fraction']['mean'])

    def test_single_full_pool_is_distinct_from_repeated_tiers(self):
        for study, total, full in (('chaksu', 501, 201), ('riga', 401, 181)):
            rows = self.data['warmup'][study]
            self.assertEqual(sum(x['replicates'] for x in rows), total)
            self.assertEqual((rows[-1]['replicates'], rows[-1]['n']), (1, full))
            self.assertTrue(all(x['replicates'] == 100 for x in rows[:-1]))
            for row in rows:
                for field in ('lambda', 'raw_omission_percent', 'area_percent'):
                    self.assertLessEqual(row[field]['p05'], row[field]['median'])
                    self.assertLessEqual(row[field]['median'], row[field]['p95'])

    def test_adverse_slice_and_source_exceedances_remain_visible(self):
        mag = next(x for x in self.data['sources']['riga'] if x['source'] == 'MAGRABI' and x['origin'] == 'local')
        self.assertEqual(mag['images'], 23)
        self.assertGreater(mag['raw_omission_percent'], 10)
        source = next(x for x in self.data['final']['chaksu'] if x['budget_percent'] == 5)
        self.assertGreater(source['raw_omission_percent'], 5)

    def test_figure_input_corruption_and_wrong_policy_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'plot_data.json'
            path.write_text(json.dumps(self.data), encoding='utf-8')
            self.assertEqual(verify_figure_data(path)['status'], 'PASS')
            changed = copy.deepcopy(self.data)
            changed['final']['riga'][0]['origin'] = 'local' if changed['final']['riga'][0]['origin'] == 'transferred' else 'transferred'
            path.write_text(json.dumps(changed), encoding='utf-8')
            with self.assertRaises(ValueError):
                verify_figure_data(path)
            changed = copy.deepcopy(self.data)
            changed['primary_area_ratio'] += .001
            path.write_text(json.dumps(changed), encoding='utf-8')
            with self.assertRaises(ValueError):
                verify_figure_data(path)


if __name__ == '__main__':
    unittest.main()
