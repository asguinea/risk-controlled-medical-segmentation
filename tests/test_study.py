import copy
from pathlib import Path
import tempfile
import unittest

from risk_controlled_segmentation.cli import demo
from risk_controlled_segmentation.study import load_evidence, verify_chaksu, report_chaksu, markdown_report, compare
from risk_controlled_segmentation.warmup import summarize_warmup, percentile


class StudyTests(unittest.TestCase):
    def test_frozen_calibrations_and_all_warmup_summaries(self):
        result=verify_chaksu()
        self.assertEqual([x['lambda_index'] for x in result['final_decisions']],[199,22,9,4])
        self.assertEqual(result['warmup_aggregate_runs'],501)

    def test_single_full_pool_not_repeated_tier(self):
        e=load_evidence(); summary=summarize_warmup(e['warmup_runs']['runs'])
        self.assertEqual(summary['curve'][-1]['replicate_count'],1)
        self.assertEqual([r['n'] for r in summary['stability']['by_n']],[20,50,100,150,200])
        self.assertIsNone(summary['stability']['relative_reduction_n20_to_n200']['all_omega_rate'])

    def test_quantile_interpolation(self):
        self.assertEqual(percentile([0,10],.05),.5)
        self.assertEqual(percentile([3],.95),3)
        self.assertEqual(percentile([10,0,5],.25),2.5)
        with self.assertRaises(ValueError):percentile([], .5)

    def test_tampered_evidence_rejected(self):
        from importlib.resources import files
        root=files('risk_controlled_segmentation').joinpath('evidence/chaksu')
        with tempfile.TemporaryDirectory() as directory:
            temp=Path(directory)
            for item in root.iterdir():
                if item.name.endswith('.json'):(temp/item.name).write_bytes(item.read_bytes())
            with (temp/'calibration_curve.json').open('ab') as stream:stream.write(b' ')
            with self.assertRaisesRegex(ValueError,'hash mismatch'):verify_chaksu(temp)

    def test_structural_comparison_and_tolerance(self):
        compare({'risk':.05},{'risk':.05+1e-14})
        for a,b in (({'risk':.05},{'risk':.050001}),({'n':True},{'n':1}),({'x':1,'y':2},{'x':1}),('1/2','2/4')):
            with self.assertRaises(ValueError): compare(a,b)

    def test_summary_change_detected(self):
        e=load_evidence(); altered=copy.deepcopy(e['warmup_runs']['runs']); altered[0]['lambda']+=.1
        with self.assertRaises(ValueError):compare(summarize_warmup(altered),e['warmup_expected'])

    def test_report_retains_observed_exceedance_and_denominators(self):
        report=markdown_report(report_chaksu())
        self.assertIn('5.3732%',report); self.assertIn('50/204',report)
        self.assertIn('201 | 1 |',report); self.assertIn('not pixel-level reruns',report)

    def test_synthetic_demo_padding_and_endpoint(self):
        d=demo(); self.assertTrue(d['synthetic'])
        self.assertEqual(d['regions'][-1]['included_valid_positions'],list(range(5)))
        self.assertEqual(d['regions'][-1]['raw_omission'],'0/1')


if __name__=='__main__':unittest.main()
