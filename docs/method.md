# Expected omission control

For image i, expert e supplies a positive raster mask with area a. A predicted region omits m of its pixels. Raw expert omission is `m/a`. Each expert's loss is rounded upward to a multiple of 1/10,000, then averaged equally over the panel. Chákṣu has five experts, giving an integer numerator over 50,000 for each image. This gives the small and large expert masks equal weight; pooling reference pixels would define a different loss.

Let `Q_i(λ)` denote that bounded image loss. The historical family includes every grid point `λ=t/1000`, t=0,…,1000. A valid pixel belongs to the region when its frozen score is `>=1−λ`. Padding lies outside Ω. Increasing λ expands the region and cannot increase omission. The all-Ω endpoint has zero omission. No prediction morphology is applied.

With n calibration images, choose the smallest grid value such that:

`(sum_i Q_i(λ) + 1) / (n + 1) <= α`.

The public implementation compares integer cross-products and formats reduced rational results. The full grid is required: omitted candidates could change the chosen smallest admissible region. A candidate exactly at the inequality boundary passes; adding one loss quantum can change that decision. If none passes, return all Ω with `certified=false`. This flag describes the finite-sample criterion; the endpoint still has known zero omission.

The expectation statement averages over the calibration data and a new exchangeable image. Monotone bounded losses, the valid endpoint, and the fixed scoring/region construction are part of the assumptions. It is not a statement that each calibration produces a risk bound with 95% confidence. No delta parameter or exact-binomial selected-risk test is used. Upward quantization dominates raw raster loss pointwise by less than 0.0001, so the expected quantized-loss guarantee also bounds raw omission under the same assumptions. See [Conformal Risk Control, method and Theorem 1](https://arxiv.org/html/2208.02814v4).

Neither an individual image, its worst expert, a device subgroup, nor an unidentified patient is the controlled quantity. Fixed-panel expert masks are the reference, not a claim of clinical truth. Calibration/evaluation role separation does not by itself establish exchangeability of related images. A source-population guarantee does not automatically extend to a new dataset.

## APIs and reference comparison

`quantized_omission(missed, area)` returns the exact upward-rounded loss. `image_omission(counts, expected_experts=5)` returns the raw and quantized equal-expert average for **one image**.

`aggregate_image_losses(image_numerators, loss_denominator=50000)` checks each image's complete loss curve for bounds, monotonicity and zero endpoint, then sums it. It cannot establish that the inputs faithfully represent source annotations or exchangeable images.

`calibrate_aggregate(totals, loss_denominator=50000, n_images=201, alpha="1/20")` validates aggregate structure and replays the decision. It cannot establish individual monotonicity from the sums. Floats are rejected for exact rational inputs; use rational strings or `fractions.Fraction`.

The preserved TypeScript engine uses the legacy fields `patient_losses` and `calibration_patient_count`, and fallback value `ALL_LABELS`. For this study the adapter maps one image to one such unit and the fallback to all Ω. Public Python fields use images and `ALL_OMEGA`. The reference itself remains byte-identical. The Python API intentionally accepts a complete uniformly spaced grid and integer loss numerators; it is not a drop-in replacement for every general TypeScript input shape.

`rcms demo` uses exact synthetic scores, five toy masks and an excluded padding position to illustrate nesting and omission. It does not implement the historical float32 model/raster decoder or produce new medical results.
