# Risk-controlled medical segmentation

**How much expert-defined anatomy can a predicted region omit—and how large must that region become to limit the omission?**

This repository studies uncertainty quantification for **retinal optic-cup segmentation** through omission risk, expert disagreement, region size and calibration transfer. The first release follows **Chákṣu → RIGA**, using one frozen scorer and five/six individual expert references. PolypGen is a later expansion.

At a 5% omission budget, the frozen Chákṣu policy returns regions averaging **0.6685% of valid image area**. Observed omission on 204 held-out images is **5.3732%**. The reference averages five individual experts per image; it does not require every expert's mask to be covered equally well. [Read the generated study report](experiments/chaksu/report.md).

On the **same 182 RIGA evaluation images**, the transferred 5% policy has **19.4384% omission** against six experts. Local recalibration lowers that to **3.4541%**, while mean region area expands **4.88-fold** with the same scorer. This quantifies the spatial cost of lowering omission in the target study. [Read the transfer report](experiments/riga/report.md).

![On 182 RIGA images, omission drops from 19.44% to 3.45% after local recalibration, while mean region area grows from 0.36% to 1.77% of valid image area.](docs/figures/transfer_tradeoff.png)

Follow the [research story](docs/research-story.md) for the four-budget tradeoffs, calibration-label experiments and disagreement/source slices. The [figure gallery](docs/figures/README.md) provides five reproducible SVG/PNG pairs, including a synthetic spatial explanation. The full reports retain the observed budget exceedances and small-sample limitations.

## Run the research artifact

Python 3.11 or newer is required. The base package has **no third-party runtime dependencies**, and replay requires no dataset downloads, model weights or GPU. From the repository or unpacked source archive:

Download the source archive from [v0.1.0](https://github.com/asguinea/risk-controlled-medical-segmentation/releases/tag/v0.1.0), or clone that version with `git clone --branch v0.1.0 https://github.com/asguinea/risk-controlled-medical-segmentation.git` and enter its directory. Then:

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

To render the figures:

```sh
python -m pip install ".[figures]"
rcms figures --output results/figures
rcms verify-figures docs/figures/plot_data.json
```

The [reproduction contract](docs/reproduction.md) includes the complete dependency lock and isolated source/wheel checks. Installation may download Python packages; all study commands and rendering run offline.

## What is reproducible

| Component | Available now |
| --- | --- |
| Bounded omission-risk calibration | Exact integer/rational method and synthetic examples |
| Chákṣu final calibration | Full 1,001-candidate aggregate loss curve; four budget decisions |
| Chákṣu warm-up | 501 aggregate runs; descriptive percentiles, stability and milestones |
| RIGA transfer and recalibration | Four source-policy transfers; 1,001-candidate local calibration curve and four new decisions; eight final policy evaluations |
| RIGA warm-up | 401 aggregate runs; descriptive percentiles, stability and milestones |
| Evaluation reports | Frozen aggregate outcomes, device slices and expert-disagreement slices |
| Figures | Five SVG/PNG pairs generated from verified aggregates and a synthetic example |
| Training, inference and annotation processing | Historical protocol documentation; execution is outside this artifact |

The evidence supports **calibration replay and aggregate report reproduction**. It does not reconstruct the original pixel arrays, source assignments or individual annotations. There is no patient-level, per-image coverage, worst-expert or clinical deployment guarantee. The statistical statement concerns **expected image-average omission**, under the method's assumptions; no delta or 95% high-probability risk statement applies here. Source certificates do not automatically transfer to RIGA. See the [method](docs/method.md), [Chákṣu protocol](experiments/chaksu/protocol.md), [RIGA protocol](experiments/riga/protocol.md) and [reproduction contract](docs/reproduction.md).

## Validation

```sh
python -m unittest discover -s tests -v
python scripts/verify_reference.py
```

The optional reference comparison requires Node.js 22.18 or newer with native TypeScript support. It compares 2,000 synthetic cases to the preserved original TypeScript engine without installing npm packages. The 34 Python tests include 10,000 exact quantization checks, 1,000 independent Fraction-oracle cases, decision boundaries, fallback behavior, six-expert weighting, transfer semantics and evidence/figure corruption checks.

The release check exercises the installed wheel from an unrelated environment and the tests/reference scripts from its source archive. It verifies report text, plotted data, figure regeneration, package contents and reachable Git history. The [research workflow](https://github.com/asguinea/risk-controlled-medical-segmentation/actions/workflows/research.yml) runs on Linux, macOS and Windows, with an additional Python 3.14 check on Linux. Release assets include a verification receipt identifying the tested commit, CI run and artifact hashes.

## Research context and credit

This research artifact was prepared by [Alejandro Sanchez Guinea](https://github.com/asguinea), founder of EyeTrustAI, from experiments conducted during EyeTrustAI's development research. Its contribution is the reproducible study of omission, region size, expert disagreement and calibration requirements.

The calibration method builds on **Conformal Risk Control** by Angelopoulos, Bates, Fisch, Lei and Schuster. The Chákṣu dataset and expert annotations are credited to **J. R. Harish Kumar and coauthors**, and the RIGA deposit to **Ahmed Almazroa and the dataset contributors and expert annotators**. The historical scorer uses U-Net with a ResNet34 encoder; these established methods and datasets are not contributions of this repository. See [third-party credit](THIRD_PARTY_NOTICES.md) and [license scope](LICENSE_SCOPE.md).

The original software and analytical material are offered under Apache-2.0. Source datasets and model weights are not distributed. RIGA's source catalog records CC BY-NC 4.0; the study covers only the 679/750 images with extractable six-expert references. The source-asset restrictions and provenance limits are explicit in the [RIGA reproduction contract](experiments/riga/reproduction.md).

Use [CITATION.cff](CITATION.cff) for software attribution and cite the underlying methods and datasets separately. The [v0.1.0 release](https://github.com/asguinea/risk-controlled-medical-segmentation/releases/tag/v0.1.0) provides versioned source and wheel downloads, a verification receipt and checksums. See the [release notes](docs/releases/v0.1.0.md) for scope and reproduction instructions.
