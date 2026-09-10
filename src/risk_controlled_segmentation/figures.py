"""Publication figures from verified aggregates and an explicitly synthetic toy.

Plotting imports are lazy: evidence replay and figure-data verification use only
the standard library. No pixel-level study material is read or reconstructed.
"""
import json
from fractions import Fraction
from pathlib import Path

from .study import compare, report_chaksu
from .method import image_omission, rational_text
from .riga import report_riga

STEMS = ('transfer_tradeoff', 'risk_area_budgets', 'calibration_size',
         'disagreement_and_sources', 'synthetic_omission')
BLUE, ORANGE, TEAL = '#2864A0', '#BE5A17', '#168174'
INK, MUTED = '#192B3C', '#546575'


def metrics(value, *, chaksu=False):
    return {
        'images': value['images'],
        'raw_omission_percent': 100 * value['risk'][
            'raw_average_omission' if chaksu else 'raw_average'],
        'area_percent': 100 * value['spatial_utility']['region_area_fraction']['mean'],
        'expert_normalized_size': value['reference_normalized']['normalized_region_size']['mean'],
    }


def figure_data():
    """Project only displayed quantities from integrity-checked, replayed reports."""
    from .cli import demo
    chaksu, riga = report_chaksu(), report_riga()
    final = {'chaksu': [], 'riga': []}
    for row in chaksu['final']['controllers']:
        final['chaksu'].append({
            'budget_percent': 100 * float(Fraction(row['calibration']['alpha'])),
            'origin': 'local', **metrics(row['locked'], chaksu=True)})
    for row in riga['final']['policies']:
        final['riga'].append({
            'budget_percent': 100 * float(Fraction(row['alpha'])),
            'origin': row['origin'], **metrics(row['evaluation'])})
    warmup = {}
    for study, report in (('chaksu', chaksu), ('riga', riga)):
        rows = []
        for row in report['warmup']['curve']:
            fields = {
                'lambda': row['lambda'],
                'raw_omission_percent': row['evaluation']['raw_omission'] if study == 'chaksu' else row['raw_omission'],
                'area_percent': row['spatial_utility']['mean_region_area_fraction'] if study == 'chaksu' else row['mean_area_fraction'],
            }
            rows.append({'n': row['n'],
                         'replicates': row['replicate_count'] if study == 'chaksu' else row['replicates'],
                         **{key: {q: stats[q] * (1 if key == 'lambda' else 100)
                                  for q in ('p05', 'median', 'p95')}
                            for key, stats in fields.items()}})
        warmup[study] = rows
    disagreement = {'chaksu': [], 'riga': []}
    ch_strata = chaksu['final']['primary_disagreement']['by_stratum']
    for level in ('LOW', 'MEDIUM', 'HIGH'):
        value = ch_strata[level + '_DISAGREEMENT']
        disagreement['chaksu'].append({'stratum': level, 'origin': 'local',
                                      **metrics(value, chaksu=True)})
    primary = [p for p in riga['final']['policies'] if p['alpha'] == '1/20']
    for policy in primary:
        for level in ('LOW', 'MEDIUM', 'HIGH'):
            disagreement['riga'].append({'stratum': level, 'origin': policy['origin'],
                                        **metrics(policy['disagreement']['by_stratum'][level])})
    sources = {
        'chaksu': [{'source': name, 'origin': 'local', **metrics(value, chaksu=True)}
                   for name, value in chaksu['final']['primary_devices'].items()],
        'riga': [{'source': name, 'origin': p['origin'], **metrics(p['by_source'][name])}
                 for p in primary for name in ('MESSIDOR', 'BIN_RUSHED', 'MAGRABI')],
    }
    synthetic = demo()
    synthetic['expert_masks'] = [[0, 1], [0, 1, 2], [1, 2], [0, 2], [1, 2, 3]]
    for row in synthetic['regions']:
        selected = set(row['included_valid_positions'])
        raw, quantized = image_omission([(len(set(mask) - selected), len(mask))
                                        for mask in synthetic['expert_masks']], expected_experts=5)
        compare(rational_text(raw), row['raw_omission'])
        compare(rational_text(quantized), row['quantized_omission'])
    return {'schema': 'RCMS_FIGURES_V1', 'final': final, 'warmup': warmup,
            'disagreement': disagreement, 'sources': sources,
            'primary_area_ratio': riga['verification']['primary_comparison']['local_over_transferred']['mean_area_fraction'],
            'synthetic': synthetic}


def verify_figure_data(path):
    expected = json.loads(Path(path).read_text(encoding='utf-8'))
    compare(figure_data(), expected)
    return {'status': 'PASS', 'figure_pairs': len(STEMS),
            'floating_point_absolute_tolerance': 1e-12,
            'note': 'Verified plotted quantities; rendering bytes may vary across platforms.'}


def generate_figures(output):
    data = figure_data()
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from matplotlib.patches import Patch, Rectangle
        from matplotlib.ticker import FixedLocator, FuncFormatter, NullLocator
    except ImportError as error:
        raise ValueError('Figure rendering requires the figures extra: pip install ".[figures]"') from error
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    style = {
        'font.family': 'DejaVu Sans', 'font.size': 10, 'text.color': INK,
        'axes.labelcolor': INK, 'axes.edgecolor': '#C6CFD6',
        'axes.titleweight': 'bold', 'axes.titlesize': 11,
        'axes.spines.top': False, 'axes.spines.right': False,
        'xtick.color': MUTED, 'ytick.color': MUTED, 'grid.color': '#E3E8ED',
        'axes.axisbelow': True, 'savefig.facecolor': 'white',
        'svg.hashsalt': 'rcms-v0.1.0', 'svg.fonttype': 'none',
    }

    def frame(fig, title, subtitle, footer, *, top=.78, bottom=.18):
        fig.suptitle(title, x=.075, y=.97, ha='left', fontsize=19, weight='bold')
        fig.text(.075, .885, subtitle, fontsize=10, color=MUTED, va='top')
        fig.text(.075, .025, footer, fontsize=9, color=MUTED, va='bottom', linespacing=1.5)
        fig.subplots_adjust(left=.09, right=.97, top=top, bottom=bottom, wspace=.35, hspace=.6)

    def save(fig, stem):
        svg = output / (stem + '.svg')
        fig.savefig(svg, metadata={'Date': None, 'Creator': 'risk-controlled-medical-segmentation'})
        # Matplotlib emits trailing spaces in path data; normalize only line ends.
        svg.write_text('\n'.join(line.rstrip() for line in svg.read_text(encoding='utf-8').splitlines()) + '\n', encoding='utf-8')
        fig.savefig(output / (stem + '.png'), dpi=180, metadata={'Software': 'risk-controlled-medical-segmentation'})
        plt.close(fig)

    def policies(study, origin):
        return sorted((x for x in data['final'][study] if x['origin'] == origin),
                      key=lambda x: x['budget_percent'])

    with plt.rc_context(style):
        fig, axes = plt.subplots(1, 2, figsize=(11.5, 5.3))
        primary = [next(x for x in policies('riga', origin) if x['budget_percent'] == 5)
                   for origin in ('transferred', 'local')]
        for ax, field, title in zip(axes, ('raw_omission_percent', 'area_percent'),
                                   ('Mean raw omission (%)', 'Mean region / valid image (%)')):
            values = [x[field] for x in primary]
            bars = ax.bar([0, 1], values, width=.58, color=[ORANGE, BLUE])
            ax.bar_label(bars, labels=[f'{v:.2f}%' for v in values], label_type='center', color='white', weight='bold', fontsize=13)
            ax.set_xticks([0, 1], ['Transferred\nChákṣu policy', 'Local RIGA\nrecalibration'])
            ax.set_title(title, loc='left', pad=16)
            ax.set_ylim(0, max(values) * 1.32)
            ax.grid(axis='y')
        axes[0].axhline(5, color=MUTED, ls='--', lw=1)
        axes[0].text(.98, 5.8, '5% calibration budget', fontsize=9, color=MUTED, ha='right',
                     transform=axes[0].get_yaxis_transform(), bbox={'facecolor': 'white', 'edgecolor': 'none', 'pad': 2})
        frame(fig, 'Lower omission has a spatial cost',
              f'RIGA · same 182 locked images · six experts · frozen scorer · {data["primary_area_ratio"]:.2f}× mean region area after recalibration',
              'Both policies originate from a 5% calibration budget. The source certificate does not transfer to RIGA.\n'
              'Omission is averaged over experts within each image, then over images. Retrospective policy comparison; no clinical effect is estimated.')
        save(fig, 'transfer_tradeoff')

        fig, axes = plt.subplots(2, 2, figsize=(11.5, 8.3))
        for col, (study, label) in enumerate((('chaksu', 'Chákṣu · 204 images · five experts'), ('riga', 'RIGA · 182 images · six experts'))):
            for origin, color, marker in (('transferred', ORANGE, 's'), ('local', BLUE, 'o')):
                rows = policies(study, origin)
                if not rows:
                    continue
                for row, field in enumerate(('raw_omission_percent', 'area_percent')):
                    axes[row, col].plot([1, 5, 10, 20], [x[field] for x in rows], color=color, marker=marker, label=origin.title())
            axes[0, col].plot([1, 5, 10, 20], [1, 5, 10, 20], color=MUTED, ls='--', lw=1, label='Calibration budget')
            axes[0, col].set_title(label, loc='left', pad=12)
            axes[0, col].set_ylim(bottom=0)
            axes[0, col].legend(fontsize=9, frameon=False)
            axes[1, col].set_yscale('log')
            axes[1, col].yaxis.set_major_locator(FixedLocator([.5, .6, .7, .8, .9] if study == 'chaksu' else [.2, .5, 1, 2, 5, 10]))
            axes[1, col].yaxis.set_major_formatter(FuncFormatter(lambda value, pos: f'{value:g}'))
            axes[1, col].yaxis.set_minor_locator(NullLocator())
            for row in range(2):
                ax = axes[row, col]
                ax.set_xticks([1, 5, 10, 20])
                ax.set_xlabel('Calibration omission budget (%)')
                ax.set_ylabel('Mean raw omission (%)' if row == 0 else 'Mean region / valid image (%) · log scale')
                ax.grid(axis='y', which='both', alpha=.7)
        frame(fig, 'The risk–area tradeoff across four budgets',
              'Final locked evaluations. Each column retains its own image population and expert reference.',
              'Dashed line: calibration target, not a finite-test or per-image upper bound. Area panels use logarithmic scales.\n'
              'Chákṣu exceeds the 5% and 10% targets in the observed evaluation. RIGA transfers are evaluated without a target-study certificate.', top=.79, bottom=.16)
        save(fig, 'risk_area_budgets')

        fig, axes = plt.subplots(3, 2, figsize=(11.5, 10.3))
        for col, (study, label) in enumerate((('chaksu', 'Chákṣu · fixed 134-image development evaluation'), ('riga', 'RIGA · fixed 135-image development evaluation'))):
            rows = data['warmup'][study]
            repeated, full = rows[:-1], rows[-1]
            for row, (field, ylabel) in enumerate((('lambda', 'Selected λ'), ('raw_omission_percent', 'Mean raw omission (%)'), ('area_percent', 'Mean region / valid image (%)'))):
                ax = axes[row, col]
                xs = list(range(len(repeated)))
                ax.fill_between(xs, [x[field]['p05'] for x in repeated], [x[field]['p95'] for x in repeated], color=BLUE, alpha=.18)
                ax.plot(xs, [x[field]['median'] for x in repeated], 'o-', color=BLUE)
                ax.plot(len(repeated), full[field]['median'], 'D', mfc='white', mec=INK, ms=7)
                ax.axvline(len(repeated) - .5, color='#BCC7D0', ls=':', lw=1)
                ax.set_xticks(range(len(rows)), [str(x['n']) for x in repeated] + [f'{full["n"]}\nfull pool'])
                ax.set_ylabel(ylabel)
                ax.grid(axis='y')
                ax.set_ylim(bottom=0)
                if row == 0:
                    ax.set_ylim(0, 1.05)
                    ax.set_title(label, loc='left', fontsize=10, pad=10)
                if row == 2:
                    ax.set_xlabel('Calibration images (tiers spaced evenly)')
        frame(fig, 'More calibration labels do not ensure stability',
              '5% budget · blue: median and 5th–95th percentiles over 100 runs per repeated tier · hollow diamond: one full-pool run',
              'Repeated runs reuse development pools; bands are descriptive, not confidence intervals. These are not the locked final evaluations.\n'
              'Columns use different omission and area scales. Chákṣu stabilizes within this design; RIGA remains variable.', top=.80, bottom=.14)
        save(fig, 'calibration_size')

        fig, axes = plt.subplots(2, 2, figsize=(11.5, 8.6))
        for col, (study, title) in enumerate((('chaksu', 'Chákṣu · five experts'), ('riga', 'RIGA · six experts'))):
            origins = [('local', BLUE, 'o')] if study == 'chaksu' else [('transferred', ORANGE, 's'), ('local', BLUE, 'o')]
            for origin, color, marker in origins:
                rows = [x for x in data['disagreement'][study] if x['origin'] == origin]
                axes[0, col].plot(range(3), [x['expert_normalized_size'] for x in rows], color=color, marker=marker, label=origin.title())
                labels = [f'{x["stratum"].title()}\nn={x["images"]}' for x in rows]
                axes[0, col].set_xticks(range(3), labels)
                src = [x for x in data['sources'][study] if x['origin'] == origin]
                axes[1, col].plot(range(3), [x['raw_omission_percent'] for x in src], color=color, marker=marker, ls='none', label=origin.title(), ms=7)
                source_labels = [f'{x["source"].replace("BIN_RUSHED", "Bin Rushed").title()}\nn={x["images"]}' for x in src]
                axes[1, col].set_xticks(range(3), source_labels)
            axes[0, col].set_title(title, loc='left', pad=12)
            axes[0, col].set_xlabel('Expert-disagreement stratum')
            axes[0, col].set_ylabel('Mean expert-normalized region size')
            axes[1, col].set_ylabel('Mean raw omission (%)')
            axes[1, col].set_xlabel('Device' if study == 'chaksu' else 'Source')
            axes[1, col].axhline(5, color=MUTED, ls='--', lw=1)
            for row in range(2):
                points = data['disagreement'][study] if row == 0 else data['sources'][study]
                field = 'expert_normalized_size' if row == 0 else 'raw_omission_percent'
                axes[row, col].set_ylim(0, max(x[field] for x in points) * 1.16)
                axes[row, col].grid(axis='y')
                axes[row, col].legend(fontsize=9, frameon=False)
        frame(fig, 'Pooled results leave important variation visible',
              'Final 5% policies · disagreement strata use predeclared development cutpoints · all slices are descriptive',
              'Expert-normalized size: region area / mean expert cup area within each image, then averaged over images. Different column scales.\n'
              'Dashed line: 5% calibration budget, not a subgroup guarantee. Magrabi local omission is 10.35% (n=23); small slices are not rankings.', top=.78, bottom=.17)
        save(fig, 'disagreement_and_sources')

        fig, axes = plt.subplots(1, 4, figsize=(11.5, 5.1))
        masks = data['synthetic']['expert_masks']
        for ax, row in zip(axes, data['synthetic']['regions']):
            selected = set(row['included_valid_positions'])
            for expert, mask in enumerate(masks):
                for pixel in range(6):
                    color = '#E9EDF1' if pixel == 5 else BLUE if pixel in selected else 'white'
                    ax.add_patch(Rectangle((pixel, expert), 1, 1, facecolor=color, edgecolor='#C6CFD6', lw=.5,
                                           hatch='///' if pixel == 5 else None))
                    if pixel in mask:
                        ax.plot(pixel + .5, expert + .5, 'o', ms=6, color='white' if pixel in selected else ORANGE,
                                mec=INK, mew=.6)
            ax.set(xlim=(0, 6), ylim=(5, 0), aspect='equal')
            ax.set_xticks([.5, 1.5, 2.5, 3.5, 4.5, 5.5], ['0', '1', '2', '3', '4', 'pad'])
            ax.set_yticks([i + .5 for i in range(5)], [f'E{i+1}' for i in range(5)])
            ax.tick_params(length=0, labelsize=8)
            ax.set_title(f'λ = {row["lambda"]}', pad=12)
            ax.set_xlabel(f'Raw omission: {100 * float(Fraction(row["raw_omission"])):.1f}%\nValid area: {100 * row["valid_area_fraction"]:.0f}%', fontsize=10, labelpad=10)
        frame(fig, 'Larger nested regions omit fewer reference pixels',
              'Synthetic toy · one image represented by five valid positions and one padding position · five expert masks',
              'Each row repeats the same prediction for one expert. Dots mark reference pixels: orange = omitted; white = included.\n'
              'Expert omissions are averaged equally, after upward quantization for calibration. This toy illustrates the rule; it is not retinal evidence.', top=.76, bottom=.27)
        fig.legend(handles=[Patch(facecolor=BLUE, label='Predicted region'), Patch(facecolor='#E9EDF1', hatch='///', label='Excluded padding')],
                   loc='lower center', bbox_to_anchor=(.5, .135), ncol=2, frameon=False, fontsize=9)
        save(fig, 'synthetic_omission')
    (output / 'plot_data.json').write_text(json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + '\n', encoding='utf-8')
    return {'status': 'PASS', 'figure_pairs': len(STEMS), 'output': str(output)}
