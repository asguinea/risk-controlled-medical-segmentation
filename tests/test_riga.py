import copy
from fractions import Fraction
from importlib.resources import files
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from risk_controlled_segmentation.method import image_omission
from risk_controlled_segmentation.riga import (
    comparison, load_riga, markdown_report, report_riga, summarize_riga_warmup, validate_riga, verify_riga,
)
from risk_controlled_segmentation.study import load_evidence


class RigaTests(unittest.TestCase):
    def test_four_local_decisions_eight_policies_and_401_runs(self):
        result=verify_riga()
        self.assertEqual([x['lambda_index'] for x in result['final_decisions']],[971,530,137,32])
        self.assertEqual(result['transferred_policy_calibrations'],0)
        self.assertEqual(result['final_policies_checked'],8)
        self.assertEqual(result['warmup_aggregate_runs'],401)
        self.assertFalse(result['original_final_input_digest_available'])

    def test_six_experts_equal_weight(self):
        raw,q=image_omission([(1,1)]+[(0,100)]*5,expected_experts=6)
        self.assertEqual(raw,Fraction(1,6));self.assertEqual(q,raw)
        with self.assertRaises(ValueError):image_omission([(0,1)]*5,expected_experts=6)

    def test_five_expert_denominator_rejected(self):
        e=load_riga();e['calibration_curve']['loss_denominator']=50000
        with self.assertRaises(ValueError):validate_riga(e,load_evidence())

    def test_source_certification_not_transferred(self):
        e=load_riga();e['final']['policies'][0]['formal_riga_certificate']=True
        with self.assertRaisesRegex(ValueError,'certificate'):validate_riga(e,load_evidence())

    def test_wrong_source_threshold_rejected(self):
        e=load_riga();e['final']['policies'][0]['lambda_index']=200
        with self.assertRaises(ValueError):validate_riga(e,load_evidence())

    def test_eligibility_cannot_be_relabelled_full_dataset(self):
        e=load_riga();e['context']['eligible_images']=750
        with self.assertRaises(ValueError):validate_riga(e,load_evidence())

    def test_model_replacement_rejected(self):
        e=load_riga();e['context']['model_sha256']='0'*64
        with self.assertRaises(ValueError):validate_riga(e,load_evidence())

    def test_same_role_comparison_and_zero_ratio(self):
        e=load_riga();a,b=[x['evaluation'] for x in e['final']['policies'] if x['alpha']=='1/20']
        result=comparison(a,b)
        self.assertAlmostEqual(result['local_over_transferred']['mean_area_fraction'],4.878402248550742)
        self.assertIsNone(result['local_over_transferred']['all_omega'])
        b=copy.deepcopy(b);b['images']=135
        with self.assertRaises(ValueError):comparison(a,b)

    def test_single_full_run_excluded_from_stability(self):
        e=load_riga();s=summarize_riga_warmup(e['warmup_runs']['runs'])
        self.assertEqual(s['curve'][-1]['n'],181);self.assertEqual(s['curve'][-1]['replicates'],1)
        self.assertEqual(s['milestones']['first_n_lambda_width_below_0_2'],'NOT_OBSERVED')
        self.assertLess(s['stability']['relative_width_reduction_n20_to_n150']['lambda'],.1)

    def test_development_not_substituted_for_final(self):
        e=load_riga();e['final']['calibrations'][1]=e['development']['local_calibration']
        with self.assertRaises(ValueError):validate_riga(e,load_evidence())

    def test_changed_warmup_summary_detected(self):
        e=load_riga();e['warmup_runs']['runs'][0]['raw_omission']+=.001
        with self.assertRaises(ValueError):validate_riga(e,load_evidence())

    def test_report_preserves_tradeoff_limits_and_source_slice(self):
        rendered=markdown_report(report_riga())
        for text in ('19.4384%','3.4541%','4.88-fold','679 of 750','71 excluded','10.35%',
                     'λ=0.871','λ=0.530','no RIGA risk certificate','original historical final-input digest'):
            self.assertIn(text,rendered)

    def test_tampered_riga_evidence_rejected(self):
        root=files('risk_controlled_segmentation').joinpath('evidence/riga')
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            for item in root.iterdir():
                if item.name.endswith('.json'):(p/item.name).write_bytes(item.read_bytes())
            (p/'final.json').write_text('{}')
            with self.assertRaisesRegex(ValueError,'hash mismatch'):load_riga(p)

    def test_cli_combined_and_riga_report(self):
        result=subprocess.run([sys.executable,'-m','risk_controlled_segmentation','verify'],text=True,capture_output=True,check=True)
        payload=json.loads(result.stdout)
        self.assertEqual(payload['final_calibrations_replayed'],8)
        self.assertEqual(payload['warmup_aggregate_runs'],902)
        with tempfile.TemporaryDirectory() as d:
            subprocess.run([sys.executable,'-m','risk_controlled_segmentation','riga','--output',d],check=True,capture_output=True,text=True)
            self.assertEqual((Path(d)/'report.md').read_text(encoding='utf-8'),markdown_report(report_riga()))


if __name__=='__main__':unittest.main()
