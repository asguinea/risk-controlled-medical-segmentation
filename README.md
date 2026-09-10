# Risk-controlled medical segmentation

**How much expert-defined anatomy can a predicted region omit—and how large must that region become to limit the omission?**

This repository studies uncertainty quantification for retinal optic-cup segmentation through exact conformal risk calibration, expert disagreement and spatial utility. The current local development version contains **Chákṣu → RIGA**: a source study followed by frozen-policy transfer and target-local recalibration. PolypGen is a later expansion.

At a 5% omission budget, the frozen Chákṣu policy returns regions averaging **0.6685% of valid image area**. Observed omission on 204 held-out images is **5.3732%**. The reference averages five individual experts per image; it does not require every expert's mask to be covered equally well. [Read the generated study report](experiments/chaksu/report.md).

On the **same 182 RIGA evaluation images**, the transferred 5% policy has **19.4384% omission** against six experts. Local recalibration lowers that to **3.4541%**, while mean region area expands **4.88-fold** with the same scorer. This exposes the spatial cost of restoring omission control under the target-study assumptions. [Read the transfer report](experiments/riga/report.md).

## Run the research artifact

Python 3.11 or newer is required. The package has **no runtime dependencies**, and replay requires no dataset downloads, model weights or GPU.

```sh
python -m venv .venv
```

Activate with `source .venv/bin/activate` on macOS/Linux or `.venv\Scripts\Activate.ps1` in Windows PowerShell, then:

```sh
python -m pip install .
rcms demo
rcms verify
rcms chaksu --output results/chaksu
rcms riga --output results/riga
```

`verify` checks both studies: **eight final calibration decisions** and **902 warm-up aggregate runs**. These are reproduction counts, not pooled study results. Use `rcms verify --study chaksu` or `--study riga` to select a study. Each study command writes JSON and Markdown reports. The single full-pool warm-up run remains distinct from the 100 runs at each smaller tier.

## What is reproducible

| Component | Available now |
| --- | --- |
| Bounded omission-risk calibration | Exact integer/rational method and synthetic examples |
| Chákṣu final calibration | Full 1,001-candidate aggregate loss curve; four budget decisions |
| Chákṣu warm-up | 501 aggregate runs; descriptive percentiles, stability and milestones |
| RIGA transfer and recalibration | Four source-policy transfers; 1,001-candidate local calibration curve and four new decisions; eight final policy evaluations |
| RIGA warm-up | 401 aggregate runs; descriptive percentiles, stability and milestones |
| Evaluation reports | Frozen aggregate outcomes, device slices and expert-disagreement slices |
| Training, inference and annotation processing | Historical protocol documentation; execution is outside this artifact |

The evidence supports **calibration replay and aggregate report reproduction**. It does not reconstruct the original pixel arrays, source assignments or individual annotations. There is no patient-level, per-image coverage, worst-expert or clinical deployment guarantee. The statistical statement concerns **expected image-average omission**, under the method's assumptions; no delta or 95% high-probability risk statement applies here. Source certificates do not automatically transfer to RIGA. See the [method](docs/method.md), [Chákṣu protocol](experiments/chaksu/protocol.md), [RIGA protocol](experiments/riga/protocol.md) and [reproduction contract](docs/reproduction.md).

## Validation

```sh
python -m unittest discover -s tests -v
python scripts/verify_reference.py
```

The optional reference comparison requires Node.js 22.18 or newer with native TypeScript support. It compares 2,000 synthetic cases to the preserved original TypeScript engine without installing npm packages. The 30 Python tests include 10,000 exact quantization checks, 1,000 independent Fraction-oracle cases, decision boundaries, fallback behavior, six-expert weighting, transfer semantics and evidence corruption checks.

## Research context and credit

This research artifact was prepared by [Alejandro Sanchez Guinea](https://github.com/asguinea), founder of EyeTrustAI, from experiments conducted during EyeTrustAI's development research. Its contribution is the reproducible study of omission, region size, expert disagreement and calibration requirements.

The calibration method builds on **Conformal Risk Control** by Angelopoulos, Bates, Fisch, Lei and Schuster. The Chákṣu dataset and expert annotations are credited to **J. R. Harish Kumar and coauthors**, and the RIGA deposit to **Ahmed Almazroa and the dataset contributors and expert annotators**. The historical scorer uses U-Net with a ResNet34 encoder; these established methods and datasets are not contributions of this repository. See [third-party credit](THIRD_PARTY_NOTICES.md) and [license scope](LICENSE_SCOPE.md).

The original software and analytical material are offered under Apache-2.0. Source datasets and model weights are not distributed. RIGA's source catalog records CC BY-NC 4.0; the study covers only the 679/750 images with extractable six-expert references. The source-asset restrictions and provenance limits are explicit in the [RIGA reproduction contract](experiments/riga/reproduction.md). This is a local development candidate; figures, release review and public publication follow in subsequent batches.
