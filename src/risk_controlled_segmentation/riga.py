"""RIGA frozen-policy transfer and local calibration, with six-expert references."""
from collections import Counter
from fractions import Fraction
from importlib.resources import files

from .method import calibrate_aggregate, exact
from .study import compare, load_evidence, require, verify_chaksu
from .warmup import distribution

BUDGETS=('1/100','1/20','1/10','1/5')
SOURCES=('MESSIDOR','BIN_RUSHED','MAGRABI')
WIDTHS=('lambda','raw_omission','quantized_omission','mean_area_fraction','normalized_size','worst_expert','all_six_95')


def load_riga(root=None):
    root=root if root is not None else files('risk_controlled_segmentation').joinpath('evidence/riga')
    return load_evidence(root)


def summarize_riga_warmup(runs):
    curve=[]
    for n in sorted({x['n'] for x in runs}):
        rows=[x for x in runs if x['n']==n]
        result={'n':n,'replicates':len(rows),'certified_count':sum(x['certified'] for x in rows),
                'nontrivial_count':sum(x['utility']=='NONTRIVIAL' for x in rows),
                'fully_vacuous_count':sum(x['utility']=='ALL_OMEGA' for x in rows)}
        for field in WIDTHS:
            stats=distribution(x[field] for x in rows)
            result[field]={**stats,'p05_p95_width':stats['p95']-stats['p05']}
        curve.append(result)
    repeated=[x for x in curve if x['replicates']>1]
    require([x['n'] for x in repeated]==[20,50,100,150],'RIGA repeated-tier scope mismatch')
    reductions={};improved=assessed=0
    for field in WIDTHS:
        start,end=[x[field]['p05_p95_width'] for x in (repeated[0],repeated[-1])]
        reductions[field]=None if start==0 else 1-end/start
        if start>0:
            assessed+=1;improved+=end<start
    first=lambda rows,predicate:next((x['n'] for x in rows if predicate(x)),'NOT_OBSERVED')
    milestones={
        'first_n_any_formal':first(curve,lambda x:x['certified_count']>0),
        'first_n_formal_at_least_90_percent':first(curve,lambda x:x['certified_count']/x['replicates']>=.9),
        'first_n_any_nontrivial':first(curve,lambda x:x['nontrivial_count']>0),
        'first_n_nontrivial_at_least_90_percent':first(curve,lambda x:x['nontrivial_count']/x['replicates']>=.9),
    }
    for limit in (.2,.1,.05,.02):
        milestones[f"first_n_lambda_width_below_{str(limit).replace('.', '_')}"]=first(repeated,lambda x:x['lambda']['p05_p95_width']<limit)
    for limit in (.25,.1,.05,.025,.01):
        milestones[f"first_n_median_mean_area_at_or_below_{str(limit).replace('.', '_')}"]=first(curve,lambda x:x['mean_area_fraction']['median']<=limit)
    return {'curve':curve,'milestones':milestones,'stability':{
        'state':'IMPROVES_WITH_N' if improved==assessed else 'REMAINS_VARIABLE' if improved==0 else 'MIXED',
        'relative_width_reduction_n20_to_n150':reductions,'dimensions_improved':improved,'dimensions_assessed':assessed}}


def check_metrics(value,n):
    compare(value['images'],n)
    raw,q=[value['risk'][k] for k in ('raw_average','quantized_average')]
    require(0<=raw<=q<=1 and q-raw<.0001+1e-12,'RIGA quantization domination mismatch')
    compare(q-raw,value['risk']['quantization_gap'])
    compare(raw,value['risk']['raw_distribution']['mean'])
    compare(q,value['risk']['quantized_distribution']['mean'])
    u,w=value['spatial_utility'],value['worst_expert']
    require(0<=u['region_area_fraction']['mean']<=1,'RIGA area outside valid support')
    require(raw<=w['omission']['mean']+1e-12<=1+1e-12,'RIGA worst-expert mean mismatch')
    require(value['reference_normalized']['normalized_region_size']['mean']>=0,'Invalid normalized size')
    pairs=[(u['all_omega_count'],u['all_omega_rate'])]
    pairs += [(x['count'],x['rate']) for x in u['area_at_or_below'].values()]
    pairs += [(w[f'all_six_{level}_count'],w[f'all_six_{level}_rate']) for level in (95,99)]
    for count,rate in pairs:
        require(type(count) is int and 0<=count<=n,'Invalid RIGA aggregate count')
        compare(count/n,rate)
    require(w['all_six_99_count']<=w['all_six_95_count'],'Invalid six-expert coverage nesting')


def check_slices(policy,n,source_counts):
    check_metrics(policy['evaluation'],n)
    compare({k:v['images'] for k,v in policy['by_source'].items()},source_counts)
    for collection in (policy['by_source'],policy['disagreement']['by_stratum']):
        require(sum(x['images'] for x in collection.values())==n,'RIGA slice population mismatch')
        for value in collection.values():check_metrics(value,value['images'])
        for metric in ('raw_average','quantized_average'):
            compare(sum(x['images']*x['risk'][metric] for x in collection.values())/n,policy['evaluation']['risk'][metric])
    d=policy['disagreement'];by=d['by_stratum']
    compare(by['HIGH']['reference_normalized']['normalized_region_size']['mean']-by['LOW']['reference_normalized']['normalized_region_size']['mean'],d['high_minus_low_normalized_size'])


def comparison(transferred,local):
    """Descriptive differences on one recorded role, not a causal or paired SE estimate."""
    require(transferred['images']==local['images'],'Comparison population count mismatch')
    def extract(x):
        return {'raw_omission':x['risk']['raw_average'],'quantized_omission':x['risk']['quantized_average'],
                'mean_area_fraction':x['spatial_utility']['region_area_fraction']['mean'],
                'median_area_fraction':x['spatial_utility']['region_area_fraction']['median'],
                'normalized_size':x['reference_normalized']['normalized_region_size']['mean'],
                'worst_expert':x['worst_expert']['omission']['mean'],'worst_expert_p95':x['worst_expert']['omission']['p95'],
                'all_six_95':x['worst_expert']['all_six_95_rate'],'all_six_99':x['worst_expert']['all_six_99_rate'],
                'all_omega':x['spatial_utility']['all_omega_rate']}
    left,right=extract(transferred),extract(local)
    return {'local_minus_transferred':{k:right[k]-left[k] for k in left},
            'local_over_transferred':{k:None if left[k]==0 else right[k]/left[k] for k in left}}


def validate_riga(e,source):
    """Validate an already integrity-checked bundle against verified Chákṣu evidence."""
    c,curve,final=e['context'],e['calibration_curve'],e['final']
    compare({k:c[k] for k in ('unit','expert_count','official_images','eligible_images','excluded_images')},
            {'unit':'IMAGE','expert_count':6,'official_images':750,'eligible_images':679,'excluded_images':71})
    compare(c['eligible_by_source'],{'MESSIDOR':398,'BIN_RUSHED':190,'MAGRABI':91})
    compare(c['official_by_source'],{'MESSIDOR':460,'BIN_RUSHED':195,'MAGRABI':95})
    compare(c['roles'],{'warmup_calibration':181,'warmup_evaluation':135,'final_calibration':181,'locked_evaluation':182})
    require(sum(c['roles'].values())==679 and c['subject_linkage_available'] is False and c['role_overlap']==0,'Image role boundary mismatch')
    require(c['locked_evaluated_after_policy_freeze'] is True,'Historical freeze boundary mismatch')
    require(c['reference']['positive_masks_required']==6 and c['reference']['fused_reference'] is False,'Six individual references required')
    for role,counts in c['roles_by_source'].items():require(sum(counts.values())==c['roles'][role],'Source-role counts mismatch')
    for key in ('model_sha256','raster_sha256'):compare(c[key],source['context'][key])
    compare({k:curve[k] for k in ('n_images','expert_count','loss_denominator','grid_denominator')},
            {'n_images':181,'expert_count':6,'loss_denominator':60000,'grid_denominator':1000})
    require(len(final['calibrations'])==4,'Expected four local calibrations')
    decisions=[]
    for alpha,recorded in zip(BUDGETS,final['calibrations']):
        actual=calibrate_aggregate(curve['totals'],loss_denominator=60000,n_images=181,alpha=alpha).as_dict()
        compare(actual,recorded);decisions.append(actual)
    policies=final['policies']
    require(len(policies)==8 and {(x['origin'],x['alpha']) for x in policies}=={(o,a) for a in BUDGETS for o in ('transferred','local')},'Eight-policy inventory mismatch')
    by_key={(x['origin'],x['alpha']):x for x in policies}
    for index,alpha in enumerate(BUDGETS):
        for origin in ('transferred','local'):
            p=by_key[origin,alpha]
            expected=decisions[index] if origin=='local' else source['final']['controllers'][index]['calibration']
            compare(p['lambda_index'],expected['lambda_index']);compare(p['lambda'],expected['lambda'])
            require(type(p['formal_riga_certificate']) is bool and p['formal_riga_certificate']==(origin=='local'),'Source certificate must not be represented as RIGA certification')
            check_slices(p,182,c['roles_by_source']['locked_evaluation'])
    for origin in ('transferred','local'):
        rows=[by_key[origin,alpha] for alpha in BUDGETS]
        for a,b in zip(rows,rows[1:]):
            require(a['lambda_index']>=b['lambda_index'],'Budget nesting mismatch')
            require(a['evaluation']['spatial_utility']['region_area_fraction']['mean']>=b['evaluation']['spatial_utility']['region_area_fraction']['mean'],'Area nesting mismatch')
            require(a['evaluation']['risk']['raw_average']<=b['evaluation']['risk']['raw_average'],'Omission nesting mismatch')
    primary=comparison(by_key['transferred','1/20']['evaluation'],by_key['local','1/20']['evaluation'])
    compare(primary,final['primary_comparison_expected'])
    runs=e['warmup_runs']['runs']
    require(Counter(x['n'] for x in runs)=={20:100,50:100,100:100,150:100,181:1},'RIGA warm-up tier mismatch')
    require(len({(x['n'],x['replicate']) for x in runs})==401,'Duplicate RIGA warm-up run')
    for run in runs:
        n=run['n'];total=exact(run['total_loss_exact']);q=exact(run['empirical_risk_exact']);adj=exact(run['adjusted_risk_exact'])
        require(0<=total<=n and q==total/n and adj==(total+1)/(n+1) and adj<=Fraction(1,20),'RIGA warm-up rational relation mismatch')
        require(run['certified'] is True and run['fallback']=='NONE','Historical warm-up certification mismatch')
        require(type(run['lambda_index']) is int and 0<=run['lambda_index']<=1000,'Invalid warm-up lambda')
        compare(run['lambda_index']/1000,run['lambda']);compare(float(q),run['calibration_quantized'])
        require(run['evaluation_images']==135,'Warm-up role mismatch')
        for raw,quant,gap in ((run['calibration_raw'],run['calibration_quantized'],run['calibration_gap']),
                              (run['raw_omission'],run['quantized_omission'],run['evaluation_gap'])):
            require(0<=raw<=quant<=1 and quant-raw<.0001+1e-12,'Warm-up quantization mismatch');compare(quant-raw,gap)
        require(type(run['all_six_95_count']) is int and 0<=run['all_six_95_count']<=135,'Invalid warm-up coverage count')
        compare(run['all_six_95_count']/135,run['all_six_95'])
        require(run['utility']==('NONTRIVIAL' if run['all_omega_count']<135 else 'ALL_OMEGA'),'Warm-up utility mismatch')
    warmup=summarize_riga_warmup(runs);compare(warmup,e['warmup_expected'])
    dev=e['development'];full=next(x for x in runs if x['n']==181);cal=dev['local_calibration']
    require(cal['n_images']==181 and cal['alpha']=='1/20' and cal['certified'] is True and cal['fallback']=='NONE','Development calibration scope mismatch')
    compare(cal['lambda_index'],full['lambda_index']);compare(float(exact(cal['lambda'])),full['lambda'])
    for key,field in (('total_loss','total_loss_exact'),('empirical_risk','empirical_risk_exact'),('adjusted_risk','adjusted_risk_exact')):compare(cal[key],full[field])
    check_slices(dev['local'],135,c['roles_by_source']['warmup_evaluation'])
    compare(dev['local']['evaluation']['risk']['raw_average'],full['raw_omission'])
    compare(dev['local']['evaluation']['spatial_utility']['region_area_fraction']['mean'],full['mean_area_fraction'])
    require(len(dev['transferred'])==4,'Development transferred inventory mismatch')
    for i,p in enumerate(dev['transferred']):
        compare(p['alpha'],BUDGETS[i]);compare(p['lambda_index'],source['final']['controllers'][i]['calibration']['lambda_index'])
        require(p['formal_riga_certificate'] is False,'Development source certificate does not transfer');check_metrics(p['evaluation'],135)
    check_slices({'evaluation':dev['transferred'][1]['evaluation'],**dev['primary_transferred_slices']},135,c['roles_by_source']['warmup_evaluation'])
    dev_compare=comparison(dev['transferred'][1]['evaluation'],dev['local']['evaluation'])['local_minus_transferred']
    compare({k:v for k,v in dev_compare.items() if k not in ('median_area_fraction','worst_expert_p95')},dev['primary_difference_expected'])
    return {'status':'PASS','final_calibrations_replayed':4,'transferred_policy_calibrations':0,'final_policies_checked':8,
            'development_transferred_policies_checked':4,'grid_candidates':1001,'warmup_aggregate_runs':401,'warmup_summary_tiers':5,
            'warmup_candidate_replay':False,'original_final_input_digest_available':False,'final_decisions':decisions,'primary_comparison':primary}


def verify_riga(root=None):
    verify_chaksu()
    return validate_riga(load_riga(root),load_evidence())


def report_riga(root=None):
    verification=verify_riga(root);e=load_riga(root)
    return {'verification':verification,'context':e['context'],'final':e['final'],'development':e['development'],
            'warmup':summarize_riga_warmup(e['warmup_runs']['runs'])}


def markdown_report(report):
    policies={(x['origin'],x['alpha']):x for x in report['final']['policies']}
    primary=report['verification']['primary_comparison']
    lines=['# RIGA: transferring and recalibrating omission control','',
        'A frozen Chákṣu scorer and four source policies were applied to RIGA. Four new local policies were calibrated '
        'on 181 RIGA images, then all eight policies were evaluated on the same 182 locked images. '
        'The public artifact replays the four local calibration decisions and regenerates aggregate reports; it does not rerun pixel-level inference.','',
        '**The 5% comparison:** observed omission falls from 19.4384% to 3.4541% with local recalibration, '
        f"while mean region area expands {primary['local_over_transferred']['mean_area_fraction']:.2f}-fold. "
        'The scorer is unchanged. This is a retrospective policy comparison, not a clinical or randomized treatment effect.','',
        '## Population and reference','',
        '**679 of 750 original images** have six unambiguously reconstructible, positive individual optic-cup masks. '
        'The 71 excluded images remain outside this evaluation. Source eligibility is MESSIDOR 398/460, Bin Rushed 190/195 and Magrabi 91/95. '
        'There is no stable subject linkage; the unit is an image. The six reconstructed references differ from Chákṣu’s five supplied masks.','',
        '## Final comparison','',
        '| Budget | Policy | λ | Calibrated locally on RIGA | Raw omission | Mean region / valid image | Expert-normalized size | All six ≥95% covered |',
        '| ---: | --- | ---: | :---: | ---: | ---: | ---: | ---: |']
    for alpha in BUDGETS:
        for origin in ('transferred','local'):
            p=policies[origin,alpha];e=p['evaluation']
            lines.append(f"| {100*float(exact(alpha)):.0f}% | {origin.title()} | {float(exact(p['lambda'])):.3f} | {'Yes' if p['formal_riga_certificate'] else 'No'} | "
                         f"{100*e['risk']['raw_average']:.4f}% | {100*e['spatial_utility']['region_area_fraction']['mean']:.4f}% | "
                         f"{e['reference_normalized']['normalized_region_size']['mean']:.4f} | {e['worst_expert']['all_six_95_count']}/182 |")
    lines += ['', 'The transferred policies retain Chákṣu’s thresholds and have **no RIGA risk certificate**. '
              'Local policies satisfy the expected-loss calibration criterion under the target-study assumptions. '
              'Neither statement is a 95% confidence guarantee or a hard cap on a particular evaluation sample. All-Ω counts are zero for every final policy.','',
              '| Local budget | Exact adjusted calibration risk | Selected grid index |','| ---: | --- | ---: |']
    for c in report['final']['calibrations']:
        lines.append(f"| {100*float(exact(c['alpha'])):.0f}% | {c['adjusted_risk']} | {c['lambda_index']} |")
    lines += ['',f"At 5%, local minus transferred omission is {100*primary['local_minus_transferred']['raw_omission']:.4f} percentage points. "
              f"Mean region area increases by {100*primary['local_minus_transferred']['mean_area_fraction']:.4f} percentage points, "
              f"and expert-normalized size expands {primary['local_over_transferred']['normalized_size']:.2f}-fold. "
              'Compact source predictions did not imply transferred omission control.','',
              '## Calibration-label experiment','',
              'Four tiers contain 100 nested-subset runs each. The full 181-image pool is calibrated once. '
              'All use the same 135-image development evaluation role. Bands are descriptive 5th–95th percentiles across reused pools.','',
              '| Calibration images | Runs | λ median [5th, 95th] | Omission median | Mean-area median |',
              '| ---: | ---: | ---: | ---: | ---: |']
    for row in report['warmup']['curve']:
        lam=row['lambda']
        lines.append(f"| {row['n']} | {row['replicates']} | {lam['median']:.4f} [{lam['p05']:.5f}, {lam['p95']:.5f}] | "
                     f"{100*row['raw_omission']['median']:.4f}% | {100*row['mean_area_fraction']['median']:.4f}% |")
    reduction=report['warmup']['stability']['relative_width_reduction_n20_to_n150']['lambda']
    lines += ['',f"All 401 recorded runs certify and are nontrivial, but λ-width contracts by only {100*reduction:.2f}% from n=20 to n=150. "
              'None of the repeated tiers reaches the predeclared λ-width milestone below 0.20. This differs from Chákṣu’s tighter parameter convergence.','',
              'The full development calibration selects λ=0.871; independent final calibration selects λ=0.530. '
              'Development/local-final observed omission is 0.3046%/3.4541%, and mean region area is 3.0195%/1.7687%. '
              'These are different calibration and evaluation roles, not a same-image before/after comparison.','',
              '## Source and expert-disagreement slices at 5%','',
              '| Source | Images | Transferred omission | Local omission | Transferred area | Local area |',
              '| --- | ---: | ---: | ---: | ---: | ---: |']
    for name in SOURCES:
        a,b=[policies[origin,'1/20']['by_source'][name] for origin in ('transferred','local')]
        lines.append(f"| {name} | {a['images']} | {100*a['risk']['raw_average']:.4f}% | {100*b['risk']['raw_average']:.4f}% | "
                     f"{100*a['spatial_utility']['region_area_fraction']['mean']:.4f}% | {100*b['spatial_utility']['region_area_fraction']['mean']:.4f}% |")
    lines += ['', 'Magrabi’s 23-image local slice retains about 10.35% omission despite the pooled 5% calibration budget. '
              'These are descriptive source slices, not source-specific guarantees or hardware rankings.','']
    for origin in ('transferred','local'):
        d=policies[origin,'1/20']['disagreement']
        lines.append(f"{origin.title()} disagreement versus normalized-size Spearman correlation is {d['spearman_d_vs_normalized_size']:.4f}; "
                     f"HIGH minus LOW normalized size is {d['high_minus_low_normalized_size']:.4f}. "
                     'The controller was not calibrated by disagreement.')
        lines.append('')
    lines += ['## Reproduction and rights boundary','',
              'Calibration uses upward-quantized mean omission across six experts, denominator 60,000, on the frozen 1,001-point grid. '
              'Expected loss is defined over images and calibration randomness under the stated assumptions. There is no patient, worst-expert, subgroup or clinical guarantee.','',
              'The final input was fingerprinted during the publication scope audit and its four results match the historically bound study record. '
              'An original historical final-input digest was not found in that record. Aggregate data cannot establish original per-image monotonicity or independently verify cohort identity. '
              'Warm-up candidate traces and source image records are not included.','',
              'The repository contains original code and aggregate analytical evidence. RIGA’s source catalog records CC BY-NC 4.0; '
              'images, marked overlays, reconstructed masks, scores and weights are excluded. The standalone deposit README remains unreviewed. '
              'This publication does not establish commercial rights to those source assets.','',
              'Source: [RIGA dataset](https://doi.org/10.7302/Z23R0R29). Method: [Conformal Risk Control](https://arxiv.org/abs/2208.02814).','']
    return '\n'.join(lines)
