# Risk-controlled medical segmentation

**How much expert-defined anatomy can a predicted region omit—and how large must that region become to limit the omission?**

This repository studies uncertainty quantification for retinal optic-cup segmentation through exact conformal risk calibration, expert disagreement and spatial utility. The current local development version contains the **Chákṣu source study**. RIGA calibration transfer is the next addition; PolypGen is a later expansion.

At a 5% omission budget, the frozen Chákṣu policy returns regions averaging **0.6685% of valid image area**. Observed omission on 204 held-out images is **5.3732%**. The reference averages five individual experts per image; it does not require every expert's mask to be covered equally well. [Read the generated study report](experiments/chaksu/report.md).

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
```

`verify` checks the evidence hashes, reproduces four final calibration decisions exactly, checks aggregate count/rate relationships, and regenerates six warm-up summary tiers from 501 run records. `chaksu` writes JSON and Markdown reports. The single full-pool warm-up run remains distinct from the 100 runs at each smaller tier.

## What is reproducible

| Component | Available now |
| --- | --- |
| Bounded omission-risk calibration | Exact integer/rational method and synthetic examples |
| Chákṣu final calibration | Full 1,001-candidate aggregate loss curve; four budget decisions |
| Chákṣu warm-up | 501 aggregate runs; descriptive percentiles, stability and milestones |
| Evaluation reports | Frozen aggregate outcomes, device slices and expert-disagreement slices |
| Training, inference and annotation processing | Historical protocol documentation; execution is outside this artifact |

The evidence supports **calibration replay and aggregate report reproduction**. It does not reconstruct the original pixel arrays, source assignments or individual annotations. There is no patient-level, per-image coverage, worst-expert or clinical deployment guarantee. The statistical statement concerns **expected image-average omission**, under the method's assumptions; no delta or 95% high-probability risk statement applies here. See the [method](docs/method.md), [Chákṣu protocol](experiments/chaksu/protocol.md) and [reproduction contract](docs/reproduction.md).

## Validation

```sh
python -m unittest discover -s tests -v
python scripts/verify_reference.py
```

The optional reference comparison requires Node.js 22.18 or newer with native TypeScript support. It compares 2,000 synthetic cases to the preserved original TypeScript engine without installing npm packages. The Python tests include 10,000 exact quantization checks, 1,000 independent Fraction-oracle cases, decision boundaries, fallback behavior and evidence corruption checks.

## Research context and credit

This research artifact was prepared by [Alejandro Sanchez Guinea](https://github.com/asguinea), founder of EyeTrustAI, from experiments conducted during EyeTrustAI's development research. Its contribution is the reproducible study of omission, region size, expert disagreement and calibration requirements.

The calibration method builds on **Conformal Risk Control** by Angelopoulos, Bates, Fisch, Lei and Schuster. The Chákṣu dataset and expert annotations are credited to **J. R. Harish Kumar and coauthors**. The historical scorer uses U-Net with a ResNet34 encoder; these established methods and datasets are not contributions of this repository. See [third-party credit](THIRD_PARTY_NOTICES.md) and [license scope](LICENSE_SCOPE.md).

The original software and analytical material are offered under Apache-2.0. Source datasets and model weights are not distributed. This is a local development candidate; a public release and its citation metadata will follow the completed transfer and release review.
