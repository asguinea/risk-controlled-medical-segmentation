# Chákṣu source protocol

The experiment uses version 2 of [Chákṣu](https://doi.org/10.6084/m9.figshare.20123135.v2). All 1,345 images have five readable, positive individual optic-cup references. Official Train/Test membership is provenance; the research uses its own frozen roles:

| Role | Images | Purpose |
| --- | ---: | --- |
| Model development | 605 | Scorer training and development |
| Warm-up calibration | 201 | Nested prefixes and one full-pool calibration |
| Warm-up evaluation | 134 | Fixed development evaluation for all warm-up rules |
| Final calibration | 201 | Four predeclared risk budgets |
| Locked evaluation | 204 | Evaluation after all four final policies were frozen |

The device population is Remidio 1,074, Bosch 145 and Forus 126. Stable subject linkage was unavailable. The formal unit remains an image; no patient grouping is inferred.

## Historical scorer and references

The frozen scorer is `CHAKSU_UNET_RESNET34_FIVE_EXPERT_CUP_V1`: an RGB U-Net with an ImageNet-pretrained ResNet34 encoder and soft training targets averaging five expert masks. Development used a 484/121 sanity split, then refit on all 605 development images for 12 fixed epochs (seed 1729). It does not use glaucoma diagnosis labels. Evaluation preserves all five experts individually rather than substituting fused masks.

Images retain aspect ratio with longest side 512 and central padding. Valid support Ω excludes padding; reference masks use nearest-neighbor resizing. The scorer, raster, loss, grid and roles remained frozen through warm-up and final evaluation. The historical Python 3.11 environment used PyTorch and segmentation-models-pytorch; those libraries and weights are not required by aggregate replay.

Disagreement is one minus the mean of the ten pairwise expert Dice values. Low/medium/high cutpoints were frozen from model development at approximately 0.1483635001 and 0.2038334358. Their associations with absolute region area and expert-normalized size are descriptive. No disagreement-specific calibration is performed.

## Calibration and evaluation

Warm-up uses 100 deterministic nested trajectories at n=20,50,100,150,200 and one full n=201 run, all at α=0.05. All 501 policies were selected before the fixed warm-up evaluation masks were used for descriptive outcomes. The full-pool controller is λ=0.025. These reused development cohorts do not support independent-replication or universal annotation-size claims.

The separate 201-image final role calibrated budgets 1%,5%,10%,20%. The primary 5% rule froze first, followed by sensitivities and a shared freeze before locked reference evaluation. Final λ values are 0.199,0.022,0.009,0.004 in ascending budget order. No retraining, new thresholds, device-specific rules, fused evaluation references, or post-locked changes were introduced.

Raw omission is averaged equally over experts within each image, then over images. Region area is divided by valid image area. Expert-normalized size divides a region's area by that image's mean expert cup area before averaging. Union-normalized size and union excess use the expert union. Worst-expert omission and all-five coverage counts remain descriptive.

The generated report preserves the final 5.3732% and 11.2165% observed omission above their respective 5% and 10% budgets. The statistical expectation guarantee is not a hard cap on every evaluation realization.

## Frozen identities

| Artifact | SHA-256 |
| --- | --- |
| Model | `e55c3a31d05c018cf39c991189c1b817e5d3c9820e240272f256ce4c2c0338a4` |
| Raster | `afd1fcd8a912540cf00a5b54510e08ed792b096b4bae8bb4044f077cb4add8d2` |
| Roles | `a8c86dd922998f1cbb0f5d797124bd1cd049e80a049a9af49faac6f62637b9a2` |
| Combined historical scores | `0cb54700b8f4ac8462dbb51b7db742fbd2625c7810cae593b0dd21c17e3b9f65` |

These hashes identify historical artifacts; they do not make the underlying inputs available or independently prove their correctness. The dataset and original expert annotations should be cited alongside this research artifact.
