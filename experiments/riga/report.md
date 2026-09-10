# RIGA: transferring and recalibrating omission control

A frozen Chákṣu scorer and four source policies were applied to RIGA. Four new local policies were calibrated on 181 RIGA images, then all eight policies were evaluated on the same 182 locked images. The public artifact replays the four local calibration decisions and regenerates aggregate reports; it does not rerun pixel-level inference.

**The 5% comparison:** observed omission falls from 19.4384% to 3.4541% with local recalibration, while mean region area expands 4.88-fold. The scorer is unchanged. This is a retrospective policy comparison, not a clinical or randomized treatment effect.

## Population and reference

**679 of 750 original images** have six unambiguously reconstructible, positive individual optic-cup masks. The 71 excluded images remain outside this evaluation. Source eligibility is MESSIDOR 398/460, Bin Rushed 190/195 and Magrabi 91/95. There is no stable subject linkage; the unit is an image. The six reconstructed references differ from Chákṣu’s five supplied masks.

## Final comparison

| Budget | Policy | λ | Calibrated locally on RIGA | Raw omission | Mean region / valid image | Expert-normalized size | All six ≥95% covered |
| ---: | --- | ---: | :---: | ---: | ---: | ---: | ---: |
| 1% | Transferred | 0.199 | No | 5.7353% | 0.8032% | 2.8160 | 131/182 |
| 1% | Local | 0.971 | Yes | 0.2114% | 8.9058% | 32.7824 | 179/182 |
| 5% | Transferred | 0.022 | No | 19.4384% | 0.3626% | 1.1831 | 23/182 |
| 5% | Local | 0.530 | Yes | 3.4541% | 1.7687% | 6.7424 | 161/182 |
| 10% | Transferred | 0.009 | No | 32.2968% | 0.2710% | 0.8590 | 5/182 |
| 10% | Local | 0.137 | Yes | 6.8795% | 0.5895% | 1.9954 | 114/182 |
| 20% | Transferred | 0.004 | No | 47.9421% | 0.1945% | 0.5915 | 0/182 |
| 20% | Local | 0.032 | Yes | 15.4818% | 0.4033% | 1.3270 | 40/182 |

The transferred policies retain Chákṣu’s thresholds and have **no RIGA risk certificate**. Local policies satisfy the expected-loss calibration criterion under the target-study assumptions. Neither statement is a 95% confidence guarantee or a hard cap on a particular evaluation sample. All-Ω counts are zero for every final policy.

| Local budget | Exact adjusted calibration risk | Selected grid index |
| ---: | --- | ---: |
| 1% | 4827/520000 | 971 |
| 5% | 272803/5460000 | 530 |
| 10% | 1091501/10920000 | 137 |
| 20% | 724291/3640000 | 32 |

At 5%, local minus transferred omission is -15.9843 percentage points. Mean region area increases by 1.4061 percentage points, and expert-normalized size expands 5.70-fold. Compact source predictions did not imply transferred omission control.

## Calibration-label experiment

Four tiers contain 100 nested-subset runs each. The full 181-image pool is calibrated once. All use the same 135-image development evaluation role. Bands are descriptive 5th–95th percentiles across reused pools.

| Calibration images | Runs | λ median [5th, 95th] | Omission median | Mean-area median |
| ---: | ---: | ---: | ---: | ---: |
| 20 | 100 | 0.9670 [0.64145, 0.98700] | 0.0256% | 7.1187% |
| 50 | 100 | 0.9450 [0.33040, 0.96305] | 0.0882% | 4.5708% |
| 100 | 100 | 0.8980 [0.43385, 0.95300] | 0.2207% | 3.3154% |
| 150 | 100 | 0.9000 [0.61370, 0.93500] | 0.2152% | 3.3387% |
| 181 | 1 | 0.8710 [0.87100, 0.87100] | 0.3046% | 3.0195% |

All 401 recorded runs certify and are nontrivial, but λ-width contracts by only 7.02% from n=20 to n=150. None of the repeated tiers reaches the predeclared λ-width milestone below 0.20. This differs from Chákṣu’s tighter parameter convergence.

The full development calibration selects λ=0.871; independent final calibration selects λ=0.530. Development/local-final observed omission is 0.3046%/3.4541%, and mean region area is 3.0195%/1.7687%. These are different calibration and evaluation roles, not a same-image before/after comparison.

## Source and expert-disagreement slices at 5%

| Source | Images | Transferred omission | Local omission | Transferred area | Local area |
| --- | ---: | ---: | ---: | ---: | ---: |
| MESSIDOR | 108 | 21.7537% | 3.4115% | 0.3092% | 1.9461% |
| BIN_RUSHED | 51 | 8.6202% | 0.4323% | 0.3189% | 1.5452% |
| MAGRABI | 23 | 32.5551% | 10.3547% | 0.7100% | 1.4309% |

Magrabi’s 23-image local slice retains about 10.35% omission despite the pooled 5% calibration budget. These are descriptive source slices, not source-specific guarantees or hardware rankings.

Transferred disagreement versus normalized-size Spearman correlation is 0.3688; HIGH minus LOW normalized size is 0.4497. The controller was not calibrated by disagreement.

Local disagreement versus normalized-size Spearman correlation is 0.3722; HIGH minus LOW normalized size is 3.9562. The controller was not calibrated by disagreement.

## Reproduction and rights boundary

Calibration uses upward-quantized mean omission across six experts, denominator 60,000, on the frozen 1,001-point grid. Expected loss is defined over images and calibration randomness under the stated assumptions. There is no patient, worst-expert, subgroup or clinical guarantee.

The final input was fingerprinted during the publication scope audit and its four results match the historically bound study record. An original historical final-input digest was not found in that record. Aggregate data cannot establish original per-image monotonicity or independently verify cohort identity. Warm-up candidate traces and source image records are not included.

The repository contains original code and aggregate analytical evidence. RIGA’s source catalog records CC BY-NC 4.0; images, marked overlays, reconstructed masks, scores and weights are excluded. The standalone deposit README remains unreviewed. This publication does not establish commercial rights to those source assets.

Source: [RIGA dataset](https://doi.org/10.7302/Z23R0R29). Method: [Conformal Risk Control](https://arxiv.org/abs/2208.02814).
