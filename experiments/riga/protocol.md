# RIGA transfer and local recalibration protocol

The source is [Retinal fundus images for glaucoma analysis: the RIGA dataset](https://doi.org/10.7302/Z23R0R29), using the corrected Bin Rushed deposit. The original 750 images have six expert-marked copies each. The research requires six unambiguous, positive reconstructed optic-cup masks per image:

| Source | Official images | Eligible | Excluded |
| --- | ---: | ---: | ---: |
| MESSIDOR | 460 | 398 | 62 |
| BIN_RUSHED | 195 | 190 | 5 |
| MAGRABI | 95 | 91 | 4 |
| Total | 750 | 679 | 71 |

These eligibility exclusions can affect which images are represented; the results do not cover all 750 originals. No stable documented subject linkage is available, so the statistical unit is an image.

## Reconstructed references

The study compares each expert-marked overlay with its original image to recover annotation pixels. It accepts a unique inner closed cup contour within the outer disc contour. Ambiguous references are left unresolved, not guessed. Limited 3×3 line closure was required for 10 of 4,500 annotations. This operation belongs to reference reconstruction, not prediction morphology. Eligible images retain six individual masks; there is no fused evaluation reference.

The masks follow the frozen Chákṣu raster protocol: aspect-preserving longest side 512, central padding, valid-image support Ω and nearest-neighbor mask resampling. Each expert's fraction of omitted reference pixels is quantized upward at denominator 10,000, then averaged equally over six experts. The image-level loss therefore has denominator 60,000. It is not a pooled-pixel loss, worst-expert loss or six independent calibration samples per image.

Disagreement is one minus mean Dice over the 15 expert pairs. Low/medium/high cutpoints were frozen from the warm-up calibration pool at 0.14958260531720297 and 0.23392791830218795. Calibration remains pooled; there are no source-specific or disagreement-specific controllers.

## Frozen roles and scorer

| Role | Images | MESSIDOR | BIN_RUSHED | MAGRABI |
| --- | ---: | ---: | ---: | ---: |
| Warm-up calibration | 181 | 108 | 51 | 22 |
| Warm-up evaluation | 135 | 77 | 41 | 17 |
| Final calibration | 181 | 105 | 47 | 29 |
| Locked evaluation | 182 | 108 | 51 | 23 |

Role assignment was frozen, outcome/score blind and not source-stratified. Roles have zero recorded overlap. This split does not establish patient independence or exchangeability on its own.

The model is exactly the Chákṣu U-Net/ResNet34 scorer trained on five-expert Chákṣu targets. Weights, normalization, raster and score maps remained frozen; RIGA introduced no retraining or fine-tuning. The 1,001-point spatial family includes valid pixels with score `>=1−λ`. It has no prediction morphology or target-specific postprocessing. Local calibration changes only λ, using the existing bounded expected-loss method.

## Transfer, warm-up and final calibration

The four transferred policies use Chákṣu's final λ values 0.199/0.022/0.009/0.004 at 1%/5%/10%/20% source budgets. They are evaluated on the 135-image RIGA development role and later on the separate 182-image final role. The source certificate is not treated as a RIGA certificate.

Target-local warm-up uses 100 nested-subset trajectories at n=20/50/100/150, followed by one full n=181 calibration, at α=0.05. All 401 selected rules are frozen before descriptive development evaluation. The full development rule is λ=0.871.

The independent final calibration role produces local λ values 0.971/0.530/0.137/0.032 at the same four budgets. All four local policies and the combined eight-policy bundle were frozen before locked reference evaluation. The final local 5% rule has exact adjusted risk `272803/5460000`. Its observed locked omission is 3.4541%; the transferred 5% rule has 19.4384% on the same images. Local mean region area is larger by a factor of 4.8784.

The policy comparison is retrospective and uses recorded common image roles. It is not a randomized clinical comparison. Development versus final local results use different roles; their differing thresholds and effect magnitudes should remain visible. Source slices, expert disagreement and worst-expert metrics are descriptive, with no subgroup guarantee.

## Artifact identities

| Artifact | SHA-256 |
| --- | --- |
| Shared Chákṣu model | `e55c3a31d05c018cf39c991189c1b817e5d3c9820e240272f256ce4c2c0338a4` |
| Shared raster protocol | `afd1fcd8a912540cf00a5b54510e08ed792b096b4bae8bb4044f077cb4add8d2` |
| RIGA roles | `42a0b36fea16b8322a0c9669060eaae9d33e698e76d0b9eb199bf30918eaf179` |
| RIGA frozen scores | `205504c2ec35954592f9b05f2e7498087719b3b7b3c586fc4d34d2cbf7383509` |
| Combined eight-policy freeze | `f6a0b3c3b00f373a0749f1a4dae5f698edf1f1d874a26c43c4574e8924966e30` |

These identifiers do not distribute the underlying assets or prove their correctness. The [reproduction contract](reproduction.md) identifies the checks possible from the public aggregates and the remaining provenance and rights limits.
