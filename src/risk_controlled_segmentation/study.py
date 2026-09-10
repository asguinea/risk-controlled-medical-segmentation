"""Read packaged aggregates, replay final decisions, and verify descriptive summaries."""
from collections import Counter
from fractions import Fraction
import hashlib
from importlib.resources import files
import json
import math

from .method import calibrate_aggregate, exact, METHOD
from .warmup import summarize_warmup

EVIDENCE_FILES = {'calibration_curve.json', 'context.json', 'development.json', 'final.json',
                  'warmup_expected.json', 'warmup_runs.json'}
FLOAT_ATOL = 1e-12


def require(condition, message):
    if not condition:
        raise ValueError(message)


def compare(actual, expected, path='root'):
    """Exact structures, integers and rational strings; absolute tolerance for floats."""
    if isinstance(expected, dict):
        require(isinstance(actual, dict) and actual.keys() == expected.keys(), f'{path}: key mismatch')
        for key in expected:
            compare(actual[key], expected[key], f'{path}.{key}')
    elif isinstance(expected, list):
        require(isinstance(actual, list) and len(actual) == len(expected), f'{path}: list mismatch')
        for index, (a, e) in enumerate(zip(actual, expected)):
            compare(a, e, f'{path}[{index}]')
    elif isinstance(expected, float):
        require(type(actual) in (int, float) and math.isfinite(actual) and math.isfinite(expected)
                and abs(actual - expected) <= FLOAT_ATOL, f'{path}: numeric mismatch')
    else:
        require(type(actual) is type(expected) and actual == expected, f'{path}: exact mismatch')


def load_evidence(root=None):
    root = root if root is not None else files('risk_controlled_segmentation').joinpath('evidence/chaksu')
    manifest = json.loads(root.joinpath('manifest.json').read_text(encoding='utf-8'))
    require(manifest['schema'] == 'rcms.evidence-manifest.v1', 'Unknown manifest schema')
    require(set(manifest['files']) == EVIDENCE_FILES, 'Unexpected manifest entries')
    result = {}
    for name, digest in manifest['files'].items():
        content = root.joinpath(name).read_bytes()
        require(hashlib.sha256(content).hexdigest() == digest, f'{name}: evidence hash mismatch')
        result[name.removesuffix('.json')] = json.loads(content)
    return result


def check_metrics(value):
    n = value['images']
    require(type(n) is int and n > 0, 'Invalid evaluation image count')
    raw = value['risk']['raw_average_omission']; q = value['risk']['quantized_average_omission']
    require(0 <= raw <= q <= 1 and q - raw < .0001 + FLOAT_ATOL, 'Invalid omission or quantization domination')
    compare(q - raw, value['risk']['quantization_gap'])
    utility, worst = value['spatial_utility'], value['worst_expert']
    pairs = [(utility['all_omega_count'], utility['all_omega_rate'])]
    pairs += [(x['count'], x['rate']) for x in utility['area_at_or_below'].values()]
    pairs += [(worst[f'all_five_{level}_covered_count'], worst[f'all_five_{level}_covered_rate']) for level in (95, 99)]
    for count, rate in pairs:
        require(type(count) is int and 0 <= count <= n, 'Invalid aggregate count')
        compare(count / n, rate)
    require(worst['all_five_99_covered_count'] <= worst['all_five_95_covered_count'], 'Invalid coverage nesting')
    require(raw <= worst['omission']['mean'] + FLOAT_ATOL <= 1 + FLOAT_ATOL, 'Invalid worst-expert mean')
    require(0 <= utility['region_area_fraction']['mean'] <= 1, 'Invalid region area')


def verify_chaksu(root=None):
    evidence = load_evidence(root)
    curve, final = evidence['calibration_curve'], evidence['final']
    compare({key: curve[key] for key in ('n_images','expert_count','loss_denominator','grid_denominator')},
            {'n_images':201,'expert_count':5,'loss_denominator':50000,'grid_denominator':1000})
    context = evidence['context']
    require(context['unit'] == 'IMAGE' and context['expert_count'] == 5 and sum(context['roles'].values()) == 1345, 'Context mismatch')
    require(len(final['controllers']) == 4, 'Expected four final policies')
    replays = []
    for row, alpha in zip(final['controllers'], ('1/100','1/20','1/10','1/5')):
        expected = row['calibration']
        require(expected['alpha'] == alpha, 'Budget order mismatch')
        actual = calibrate_aggregate(curve['totals'], loss_denominator=curve['loss_denominator'],
                                    n_images=curve['n_images'], grid_denominator=curve['grid_denominator'], alpha=alpha)
        compare(actual.as_dict(), expected)
        require(row['locked']['images'] == 204, 'Final evaluation population mismatch')
        check_metrics(row['locked'])
        replays.append(actual.as_dict())
    for collection in (final['primary_devices'], final['primary_disagreement']['by_stratum']):
        require(sum(x['images'] for x in collection.values()) == 204, 'Slice population mismatch')
        for value in collection.values(): check_metrics(value)
        mean = sum(x['images'] * x['risk']['raw_average_omission'] for x in collection.values()) / 204
        compare(mean, final['controllers'][1]['locked']['risk']['raw_average_omission'])
    runs = evidence['warmup_runs']['runs']
    require(Counter(row['n'] for row in runs) == {20:100,50:100,100:100,150:100,200:100,201:1}, 'Warm-up tier count mismatch')
    require(len({(x['n'],x['replicate']) for x in runs}) == 501, 'Duplicate warm-up run')
    for run in runs:
        n = run['n']; total = exact(run['total_loss_exact']); adjusted = exact(run['adjusted_risk_exact'])
        require(type(run['lambda_index']) is int and 0 <= run['lambda_index'] <= 1000, 'Invalid recorded warm-up lambda')
        require(type(run['certified']) is bool and run['certified'] and run['fallback'] == 'NONE', 'Historical warm-up state mismatch')
        require(0 <= total <= n and adjusted == (total + 1) / (n + 1) and adjusted <= Fraction(1,20), 'Warm-up rational relation mismatch')
        compare(run['lambda_index']/1000, run['lambda'])
        compare(float(total),run['calibration_total_loss'])
        compare(float(total/n),run['calibration_quantized'])
        compare(float(adjusted),run['calibration_adjusted'])
        require(run['evaluation_images'] == 134, 'Warm-up evaluation population mismatch')
        for prefix in ('calibration','evaluation'):
            raw,q = run[f'{prefix}_raw'],run[f'{prefix}_quantized']
            require(0 <= raw <= q <= 1 and q - raw < .0001 + FLOAT_ATOL, 'Warm-up omission mismatch')
            compare(q-raw,run[f'{prefix}_gap'])
        compare(run['all_five_95_count']/134, run['all_five_95_rate'])
    regenerated = summarize_warmup(runs)
    compare(regenerated, evidence['warmup_expected'], 'warmup')
    development = evidence['development']; full = next(x for x in runs if x['n'] == 201)
    check_metrics(development['evaluation'])
    require(development['evaluation']['images'] == 134, 'Development evaluation count mismatch')
    require(development['calibration']['lambda_index'] == full['lambda_index'] == 25, 'Full-pool development policy mismatch')
    require(exact(development['calibration']['total_loss']) == exact(full['total_loss_exact']), 'Full-pool total mismatch')
    compare(development['evaluation']['risk']['raw_average_omission'],full['evaluation_raw'])
    compare(development['evaluation']['spatial_utility']['region_area_fraction']['mean'],full['mean_area'])
    return {'status':'PASS','method':METHOD,'final_calibrations_replayed':4,'grid_candidates':1001,
            'warmup_aggregate_runs':501,'warmup_summary_tiers':6,'warmup_candidate_replay':False,
            'float_absolute_tolerance':FLOAT_ATOL,'final_decisions':replays}


def report_chaksu(root=None):
    verification = verify_chaksu(root)
    e = load_evidence(root)
    summary = summarize_warmup(e['warmup_runs']['runs'])
    return {'verification': verification,'context':e['context'],'final':e['final'],
            'development':e['development'],'warmup':summary}


def markdown_report(report):
    lines = [
        '# Chákṣu: omission risk and region size', '',
        'Generated from frozen aggregate evidence. Four final calibration decisions are replayed exactly; '
        '501 warm-up runs regenerate descriptive summaries. Evaluation metrics are frozen aggregates, not pixel-level reruns.', '',
        'The reference is the equal average of five individual expert optic-cup masks per image. '
        'Calibration has 201 images; locked evaluation has 204 different images.', '',
        '| Budget | λ | Adjusted calibration risk | Locked raw omission | Mean region / valid image | Mean expert-normalized size | All five ≥95% covered |',
        '| ---: | ---: | ---: | ---: | ---: | ---: | ---: |',
    ]
    for row in report['final']['controllers']:
        c,m = row['calibration'],row['locked']
        lines.append(f"| {100*float(exact(c['alpha'])):.0f}% | {float(exact(c['lambda'])):.3f} | "
                     f"{100*float(exact(c['adjusted_risk'])):.4f}% | {100*m['risk']['raw_average_omission']:.4f}% | "
                     f"{100*m['spatial_utility']['region_area_fraction']['mean']:.4f}% | "
                     f"{m['reference_normalized']['normalized_region_size']['mean']:.4f} | {m['worst_expert']['all_five_95_covered_count']}/204 |")
    lines += ['', '**The 5% policy has observed omission of 5.3732%.** CRC controls expected loss over calibration and a new image '
              'under the stated assumptions; it does not promise that each evaluation sample falls below the budget. '
              'There is no 95% confidence or per-image coverage claim.', '',
              'At the primary budget, mean worst-expert omission is 12.55%; only 50 of 204 images cover at least 95% of every expert mask. '
              'Larger regions reduce omission, while their area and expert-normalized size describe the spatial cost.', '',
              '## Calibration-label experiment', '',
              'Each repeated tier contains 100 nested-subset runs. Bands below are 5th–95th descriptive percentiles across runs. '
              'The full 201-image pool is calibrated once. Evaluation is the same 134-image development role.', '',
              '| Calibration images | Runs | λ median [5th, 95th] | Omission median | Mean-area median |',
              '| ---: | ---: | ---: | ---: | ---: |']
    for row in report['warmup']['curve']:
        lam=row['lambda']
        lines.append(f"| {row['n']} | {row['replicate_count']} | {lam['median']:.4f} [{lam['p05']:.5f}, {lam['p95']:.5f}] | "
                     f"{100*row['evaluation']['raw_omission']['median']:.4f}% | {100*row['spatial_utility']['mean_region_area_fraction']['median']:.4f}% |")
    lines += ['', 'All 501 recorded rules satisfy the adjusted criterion and are nontrivial. All 100 runs at n=200 select λ=0.025. '
              'Seven initially nonzero assessed widths narrow between n=20 and n=200; all-Ω rate is always zero. '
              'These observations do not establish universal label requirements.', '', '## Descriptive slices at the 5% final policy', '',
              '| Slice | Images | Raw omission | Mean region / image | Expert-normalized size |',
              '| --- | ---: | ---: | ---: | ---: |']
    slices=[(name,report['final']['primary_devices'][name]) for name in ('Remidio','Bosch','Forus')]
    slices += [(name,report['final']['primary_disagreement']['by_stratum'][name])
               for name in ('LOW_DISAGREEMENT','MEDIUM_DISAGREEMENT','HIGH_DISAGREEMENT')]
    for name,m in slices:
        lines.append(f"| {name.replace('_',' ').title()} | {m['images']} | {100*m['risk']['raw_average_omission']:.4f}% | "
                     f"{100*m['spatial_utility']['region_area_fraction']['mean']:.4f}% | {m['reference_normalized']['normalized_region_size']['mean']:.4f} |")
    d=report['final']['primary_disagreement']
    lines += ['', f"Disagreement correlates positively with expert-normalized size (Spearman {d['spearman_d_vs_normalized_region_size']:.4f}) "
              f"but negatively with absolute region area ({d['spearman_d_vs_region_area']:.4f}). These are descriptive associations. "
              'There is no device, disagreement-stratum or worst-expert guarantee; Bosch and Forus have small samples.', '',
              '## Reproduction boundary', '',
              'The public curve contains summed quantized loss at all 1,001 grid points. It supports exact selection replay, '
              'but cannot verify the original images, expert annotations, per-image monotonicity, model training or inference. '
              'Warm-up candidate traces and per-image records are not included. RIGA transfer is presented in the separate RIGA report; figures are a subsequent addition.', '',
              'Source: [Chákṣu v2](https://doi.org/10.6084/m9.figshare.20123135.v2). '
              'Method: [Conformal Risk Control](https://arxiv.org/abs/2208.02814).', '']
    return '\n'.join(lines)
