# Reproduction contract

The installed package bundles reviewed aggregate JSON in `risk_controlled_segmentation/evidence/chaksu` and `risk_controlled_segmentation/evidence/riga`. The wheel and source distribution both contain these files. Nothing is fetched at runtime. The table below describes Chákṣu; the [RIGA contract](../experiments/riga/reproduction.md) documents its six-expert reference and distinct input provenance.

| File | Meaning and verification |
| --- | --- |
| `calibration_curve.json` | Sum of image loss numerators for all 1,001 candidates, denominator 50,000, n=201. Array position t means λ=t/1000. |
| `final.json` | Independently recorded calibration results and frozen locked metrics for four budgets, plus primary device/disagreement slices. |
| `warmup_runs.json` | 501 projected aggregate runs. Replicate numbers index repeated calibration runs, not source images. Includes sufficient fields for descriptive summaries and recorded-winner rational checks. |
| `warmup_expected.json` | Historical aggregate summaries used as independent expected values. |
| `development.json` | Single full-pool development result, evaluation and slices. |
| `context.json` | Population counts, source DOI/license and reviewed artifact identifiers. |
| `manifest.json` | SHA-256 values of the six evidence files. |

The private export verified the original source bindings, full per-image final loss matrix bounds/monotonicity, and zero endpoint before summing. Only sums and reviewed aggregate statistics are included here. Public replay cannot repeat those per-image checks or verify raw images, rasterization, annotations, model scoring, role assignments or subject independence. Content hashes check identity/integrity, not empirical truth.

## Numerical verification

Final selection uses integer cross-products. Selected grid index, certification/fallback, rational total loss, empirical risk and adjusted risk must agree exactly. Warm-up winner records have their rational total/adjustment checked, but their full candidate traces are unavailable: their smallest-admissible selection is not publicly reconstructed.

All six warm-up tiers regenerate min, max, mean, population standard deviation and linear-interpolated 5th/25th/50th/75th/95th percentiles. Widths and predeclared milestones are regenerated too. Standard-library arithmetic may differ in the last binary digits from the original NumPy reductions; aggregate floating-point comparisons therefore use **absolute tolerance 1e-12**, with no tolerance on integers, structures or rational strings. This is numerical tolerance, not a statistical confidence interval.

Repeated bands describe reused warm-up pools. The n=201 point contains one calibration and is excluded from repeated-tier stability widths. Source image loss distributions, Spearman values and per-policy evaluation aggregates are preserved as recorded summaries; they are not recomputed from individual image records.

## Independent method checks

The Python tests compare integer decisions against a direct Fraction oracle over synthetic per-image losses, including very large integers. They test upward quantization, exact boundaries, all-Ω fallback, expert weighting, padding, and a counterexample where aggregate monotonicity conceals a nonmonotone image loss. The TypeScript reference comparison provides a separate implementation check on synthetic cases.

Run `rcms chaksu --output results/chaksu` or `rcms riga --output results/riga` to generate a report. The corresponding `experiments/<study>/report.md` is the checked-in rendering. `rcms verify` verifies both studies, totaling eight final calibration decisions and 902 warm-up aggregate runs. The four source policies evaluated on RIGA are not four additional calibrations. Dataset populations, expert panels and performance are not pooled.

Source images, overlays, study masks, score arrays, per-image records, source-linked assignments and weights are not bundled. Endoscopic experiments remain a later expansion. The five research figures contain aggregate charts and an explicitly synthetic mask example; see the [figure contract](figures/README.md).

## Locked release checks

The base wheel has no third-party runtime dependencies. The `figures` extra pins Matplotlib 3.10.7 and NumPy 2.4.6. [uv.lock](../uv.lock) records transitive versions and hashes, including the separate build/metadata-check tools. With uv 0.11.16 and Node.js 22.18+ available:

```sh
uv sync --locked --extra figures --group checks --python 3.11
uv run --locked --extra figures --group checks python scripts/check_distribution.py --history --output results/distribution.json
uv run --locked --extra figures --group checks python scripts/verify_reproduction.py --output results/reproduction
```

The reproduction script builds a source archive and wheel, compares their inventories and bytes with the candidate, installs the wheel into a fresh temporary environment, and runs the source archive's 34 tests and 2,000 reference comparisons against that installation. It checks both report texts and plotted inputs, renders all five figure pairs twice, and verifies determinism within that environment. Replay and rendering run with network access blocked. The base installation is exercised before plotting dependencies are installed.

The source archive contains the reports, figures, citation file, lock, tests, TypeScript reference and release documentation. The wheel contains the Python package, all aggregate evidence and the figure generator, plus distribution metadata and license files. No source checkout, dataset or GPU is needed by the installed commands.

`check_distribution.py --history` reviews all reachable commits as well as the candidate's files against the allowed content types and paths. A separate Gitleaks scan covers Git history. These checks catch specified content leaks and integrity failures; they do not prove historical exchangeability, model quality or complete absence of every possible sensitive datum.

Cross-platform checks require identical report text after newline normalization, exact integers/rationals/structures, and absolute tolerance 1e-12 on plotted floating-point inputs. Image bytes need not match between operating systems. The [research workflow](https://github.com/asguinea/risk-controlled-medical-segmentation/actions/workflows/research.yml) runs these checks on Linux, macOS and Windows, including Python 3.11 and an additional Linux/Python 3.14 job. The release verification receipt identifies the exact successful run and commit; repeated platform runs check portability, not independent empirical replication.

## Versioned downloads

[v0.1.0](https://github.com/asguinea/risk-controlled-medical-segmentation/releases/tag/v0.1.0) provides the source archive, wheel, `verification-v0.1.0.json` and `SHA256SUMS`. The receipt identifies the source-file inventory and tested commit; the checksum file covers the other three assets. GitHub's immutable release protects the published tag and uploaded assets. With a GitHub CLI version supporting release attestations, `gh release verify v0.1.0 --repo asguinea/risk-controlled-medical-segmentation` verifies the signed release identity. Hashes and signatures identify bytes, not historical scientific validity.
