# RIGA reproduction and source-asset boundary

Run `rcms verify --study riga` to verify RIGA and its Chákṣu source policy dependency. Run `rcms riga --output results/riga` to regenerate the JSON and Markdown reports. No dataset, GPU, credentials, model weights or runtime network access is required.

The package contains seven reviewed JSON files under `risk_controlled_segmentation/evidence/riga`:

| File | Public content |
| --- | --- |
| `calibration_curve.json` | All 1,001 sums of quantized image-loss numerators, denominator 60,000, final calibration n=181 |
| `final.json` | Four independently recorded local calibration results; eight final policy summaries, source/disagreement slices and expected primary differences/ratios |
| `development.json` | Four transferred-policy development summaries; one full local development calibration/evaluation and primary source/disagreement slices |
| `warmup_runs.json` | 401 aggregate run records with recorded λ, rational calibration results, coverage counts and descriptive metrics |
| `warmup_expected.json` | Historical five-tier summary distributions, widths, stability and milestone values |
| `context.json` | Dataset/reference counts, role counts, frozen model/raster identifiers and explicit provenance and rights limits |
| `manifest.json` | SHA-256 values of the six evidence files |

## What the commands verify

Four local decisions replay through the same method implementation as Chákṣu. Grid index, certification/fallback and rational total/empirical/adjusted loss must match exactly. The four transferred policies match the verified Chákṣu source decisions and are explicitly marked without RIGA certification. Eight final evaluation summaries retain a common 182-image role; source and disagreement slice counts and weighted risks agree with their pooled summaries.

The primary local-minus-transferred differences and ratios regenerate from the frozen summaries. Undefined ratios, such as zero divided by zero for all-Ω rate, remain `null`. These aggregate differences do not reconstruct per-image paired differences, covariance or causal effects. Public role counts alone cannot independently prove that the historical image identities match.

All 401 warm-up records regenerate linear-interpolated quantiles, population standard deviations, widths and predeclared milestones. Floating-point comparisons use absolute tolerance `1e-12`; integers and rational strings are exact. The repeated tiers are n=20/50/100/150. Full n=181 has one run and is excluded from the repeated-tier stability calculation. Recorded winner arithmetic is checked, but the complete warm-up candidate traces are unavailable publicly. The experiment never reaches the predeclared repeated λ-width milestone below 0.20.

## Provenance qualification

The historical D0/D1/D2 aggregate records are bound by recorded SHA-256 values. The public projections were constructed through explicit field allowlists. Before summing the final loss matrix, the private export checks all 181 complete per-image curves for integer bounds, monotonicity and zero endpoint. It does not open original image/mask/score arrays, weights or locked per-image result rows.

The final calibration input and aggregate warm-up run file match fingerprints recorded during the publication scope audit. An original historical final-input digest was **not located in the bound D2 summary**. All four final decisions and their rational results nevertheless agree with that historically bound record. The 401 runs regenerate the historically bound D1 summary. Preserve these as distinct provenance facts; neither the current fingerprint nor a public manifest retroactively establishes an unavailable historical input binding.

The public aggregates cannot repeat the original per-image monotonicity checks, mask reconstruction, eligibility decisions, model inference, role assignment or subject-linkage checks. The expected-risk result relies on the declared image-level assumptions and the fixed six-expert reference. It is not a clinical, patient-level, worst-expert or source-specific guarantee.

## Rights and attribution

The [official metadata](https://api.datacite.org/dois/10.7302/Z23R0R29) records [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) for RIGA. The metadata response reviewed for this publication matches the historical snapshot SHA-256 `9452a37442fe69bc00cad642c083f662a1c7d7a9811c41553696ea82b5bbb84d`. The source creator is Ahmed Almazroa; credit also belongs to the dataset contributors and six expert annotators.

This candidate follows the original study's aggregate-research boundary. It includes original code, explanatory text and analytical sufficient statistics, while excluding original fundus images, expert-marked copies, reconstructed masks, score maps, image-level records, source-linked assignments and model weights. It does not offer a RIGA download, training or deployment package.

The standalone deposit README remains unreviewed; the current terms review does not establish broader permissions beyond the recorded source metadata and research boundary. The repository's Apache-2.0 license does not relicense RIGA assets or grant rights for commercial reuse of them. Ownership of a personal account or EyeTrustAI does not decide whether an upstream-asset use is noncommercial. See [license scope](../../LICENSE_SCOPE.md).
