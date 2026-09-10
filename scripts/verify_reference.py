"""Compare the public Python implementation to the unchanged TypeScript engine.

Requires Node.js >=22.18 with native TypeScript stripping; no npm download.
All cases are synthetic. The legacy 'patient' field maps to one synthetic image.
"""
import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import random
import subprocess

from risk_controlled_segmentation.method import aggregate_image_losses, calibrate_aggregate


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--cases',type=int,default=2000); args=parser.parse_args()
    if args.cases < 1:parser.error('--cases must be positive')
    root=Path(__file__).resolve().parents[1]
    reference=root/'reference/bounded-monotone-expectation-crc-v1.ts'
    digest=hashlib.sha256(reference.read_bytes()).hexdigest()
    if digest!='5cf6ec497d618054dfcb7e41356ec2321f80b36cf50185f07e6ac03a596adfb2':raise ValueError('Reference bytes changed')
    rng=random.Random(1729); cases=[]; expected=[]
    for _ in range(args.cases):
        n=rng.randint(1,25); grid=rng.randint(1,8); denominator=rng.choice([5,50000,60000,10**18+3])
        rows=[]
        for _ in range(n):
            row=[rng.randint(0,denominator)]
            for _ in range(grid-1):row.append(rng.randint(0,row[-1]))
            rows.append(row+[0])
        alpha=rng.choice([Fraction(1,100),Fraction(1,20),Fraction(1,2),Fraction(9,10)])
        cases.append({'method_profile_id':'BOUNDED_MONOTONE_EXPECTATION_CRC_V1',
                      'alpha':{'numerator':str(alpha.numerator),'denominator':str(alpha.denominator)},
                      'candidates':[{'lambda':i/grid,'patient_losses':[{'numerator':str(row[i]),'denominator':str(denominator)} for row in rows]} for i in range(grid+1)]})
        totals=aggregate_image_losses(rows,loss_denominator=denominator,grid_denominator=grid)
        expected.append(calibrate_aggregate(totals,loss_denominator=denominator,n_images=n,grid_denominator=grid,alpha=alpha))
    process=subprocess.run(['node',str(root/'reference/run_reference.mts')],input=json.dumps(cases),text=True,capture_output=True,check=True)
    actual=json.loads(process.stdout)
    if len(actual)!=len(expected):raise ValueError('Reference result count mismatch')
    for a,e in zip(actual,expected):
        fields=e.as_dict()
        if not a['ok'] or a['certified']!=e.certified or a['selected_lambda']!=e.lambda_index/e.grid_denominator:
            raise ValueError('Reference decision mismatch')
        for target,source in [('empirical_total_loss','total_loss'),('empirical_risk','empirical_risk'),('adjusted_risk','adjusted_risk')]:
            if a[target]!=fields[source]:raise ValueError(f'Reference rational mismatch: {target}')
        if a['fallback_state']!=('NONE' if e.certified else 'ALL_LABELS'):raise ValueError('Reference fallback mismatch')
    print(json.dumps({'status':'PASS','synthetic_cases':args.cases,'reference_sha256':digest}))


if __name__=='__main__':main()
