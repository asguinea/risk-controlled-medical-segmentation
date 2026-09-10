# Reproduction contract

The installed package bundles reviewed aggregate JSON in `risk_controlled_segmentation/evidence/chaksu`. The wheel and source distribution both contain these files. Nothing is fetched at runtime.

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

Run `rcms chaksu --output results/chaksu` to generate the report. `experiments/chaksu/report.md` is the checked-in rendering of that output. Source images, overlays, masks, score arrays, per-image records, source-linked assignments and weights are not bundled. RIGA and endoscopic experiments are outside the current S2 implementation. Plotting and the public release package review follow in subsequent batches.
