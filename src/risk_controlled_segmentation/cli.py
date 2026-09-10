import argparse
from fractions import Fraction
import json
from pathlib import Path

from .method import image_omission, nested_region, rational_text
from .study import markdown_report, report_chaksu, verify_chaksu


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
    sub.add_parser('verify',help='Verify bundled evidence and replay four final calibrations')
    sub.add_parser('demo',help='Show a synthetic five-expert omission example')
    report=sub.add_parser('chaksu',help='Regenerate the Chákṣu report and descriptive warm-up summaries')
    report.add_argument('--output',type=Path,help='Directory for report.json and report.md; otherwise JSON on stdout')
    args=parser.parse_args()
    try:
        result=verify_chaksu() if args.command=='verify' else demo() if args.command=='demo' else report_chaksu()
        if args.command=='chaksu' and args.output:
            args.output.mkdir(parents=True,exist_ok=True)
            (args.output/'report.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')
            (args.output/'report.md').write_text(markdown_report(result),encoding='utf-8')
            print(json.dumps({'status':'PASS','output':str(args.output)}))
        else:
            print(json.dumps(result,indent=2,sort_keys=True,allow_nan=False))
    except (ValueError,KeyError,OSError) as error:
        parser.exit(1,f'rcms: {error}\n')


if __name__=='__main__':
    main()
