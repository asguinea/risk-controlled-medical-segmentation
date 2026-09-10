import argparse
from fractions import Fraction
import json
from pathlib import Path

from .method import image_omission, nested_region, rational_text
from .study import markdown_report, report_chaksu, verify_chaksu
from .riga import markdown_report as riga_markdown, report_riga, verify_riga


def demo():
    scores = [Fraction(x) for x in ('1','3/4','1/2','1/4','0','1')]
    valid = [True]*5 + [False]
    expert_masks = [{0,1},{0,1,2},{1,2},{0,2},{1,2,3}]
    rows = []
    for lam in (Fraction(0),Fraction(1,4),Fraction(1,2),Fraction(1)):
        region=nested_region(scores,valid,lambda_value=lam)
        selected={i for i,inside in enumerate(region) if inside}
        raw,q=image_omission([(len(mask-selected),len(mask)) for mask in expert_masks],expected_experts=5)
        rows.append({'lambda':rational_text(lam),'included_valid_positions':sorted(selected),
                     'raw_omission':rational_text(raw),'quantized_omission':rational_text(q),'valid_area_fraction':len(selected)/5})
    return {'synthetic':True,'description':'One toy image, five expert masks, five valid positions and one excluded padding position. This illustrates nested regions; it is not a medical result or calibration sample.', 'regions':rows}


def main():
    parser=argparse.ArgumentParser(description='Medical segmentation research: exact calibration and aggregate replay')
    sub=parser.add_subparsers(dest='command',required=True)
    verify=sub.add_parser('verify',help='Verify both studies, or select one')
    verify.add_argument('--study',choices=('all','chaksu','riga'),default='all')
    sub.add_parser('demo',help='Show a synthetic five-expert omission example')
    report=sub.add_parser('chaksu',help='Regenerate the Chákṣu report and descriptive warm-up summaries')
    report.add_argument('--output',type=Path,help='Directory for report.json and report.md; otherwise JSON on stdout')
    riga=sub.add_parser('riga',help='Regenerate RIGA transfer, local calibration and warm-up reports')
    riga.add_argument('--output',type=Path,help='Directory for report.json and report.md; otherwise JSON on stdout')
    args=parser.parse_args()
    try:
        if args.command=='verify':
            if args.study=='chaksu':result=verify_chaksu()
            elif args.study=='riga':result=verify_riga()
            else:
                chaksu_result,riga_result=verify_chaksu(),verify_riga()
                result={'status':'PASS','studies':{'chaksu':chaksu_result,'riga':riga_result},
                        'final_calibrations_replayed':8,'warmup_aggregate_runs':902,
                        'note':'Inventory totals; studies and expert references are not pooled.'}
        elif args.command=='demo':result=demo()
        else:result=report_chaksu() if args.command=='chaksu' else report_riga()
        if args.command in ('chaksu','riga') and args.output:
            args.output.mkdir(parents=True,exist_ok=True)
            (args.output/'report.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')
            render=markdown_report if args.command=='chaksu' else riga_markdown
            (args.output/'report.md').write_text(render(result),encoding='utf-8')
            print(json.dumps({'status':'PASS','output':str(args.output)}))
        else:
            print(json.dumps(result,indent=2,sort_keys=True,allow_nan=False))
    except (ValueError,KeyError,OSError) as error:
        parser.exit(1,f'rcms: {error}\n')


if __name__=='__main__':
    main()
