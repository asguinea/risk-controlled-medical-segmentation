# Chákṣu: omission risk and region size

Generated from frozen aggregate evidence. Four final calibration decisions are replayed exactly; 501 warm-up runs regenerate descriptive summaries. Evaluation metrics are frozen aggregates, not pixel-level reruns.

The reference is the equal average of five individual expert optic-cup masks per image. Calibration has 201 images; locked evaluation has 204 different images.

| Budget | λ | Adjusted calibration risk | Locked raw omission | Mean region / valid image | Mean expert-normalized size | All five ≥95% covered |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1% | 0.199 | 0.9987% | 0.7721% | 0.8970% | 1.7540 | 167/204 |
| 5% | 0.022 | 4.8616% | 5.3732% | 0.6685% | 1.2794 | 50/204 |
| 10% | 0.009 | 9.9736% | 11.2165% | 0.5705% | 1.0765 | 12/204 |
| 20% | 0.004 | 17.7955% | 19.7981% | 0.4828% | 0.8961 | 2/204 |

**The 5% policy has observed omission of 5.3732%.** CRC controls expected loss over calibration and a new image under the stated assumptions; it does not promise that each evaluation sample falls below the budget. There is no 95% confidence or per-image coverage claim.

At the primary budget, mean worst-expert omission is 12.55%; only 50 of 204 images cover at least 95% of every expert mask. Larger regions reduce omission, while their area and expert-normalized size describe the spatial cost.

## Calibration-label experiment

Each repeated tier contains 100 nested-subset runs. Bands below are 5th–95th descriptive percentiles across runs. The full 201-image pool is calibrated once. Evaluation is the same 134-image development role.

| Calibration images | Runs | λ median [5th, 95th] | Omission median | Mean-area median |
| ---: | ---: | ---: | ---: | ---: |
| 20 | 100 | 0.3935 [0.18575, 0.71530] | 1.4330% | 0.9988% |
| 50 | 100 | 0.0360 [0.02990, 0.05000] | 5.0196% | 0.7449% |
| 100 | 100 | 0.0290 [0.02400, 0.03400] | 5.7460% | 0.7214% |
| 150 | 100 | 0.0270 [0.02400, 0.02900] | 6.0325% | 0.7134% |
| 200 | 100 | 0.0250 [0.02500, 0.02500] | 6.3527% | 0.7049% |
| 201 | 1 | 0.0250 [0.02500, 0.02500] | 6.3527% | 0.7049% |

All 501 recorded rules satisfy the adjusted criterion and are nontrivial. All 100 runs at n=200 select λ=0.025. Seven initially nonzero assessed widths narrow between n=20 and n=200; all-Ω rate is always zero. These observations do not establish universal label requirements.

## Descriptive slices at the 5% final policy

| Slice | Images | Raw omission | Mean region / image | Expert-normalized size |
| --- | ---: | ---: | ---: | ---: |
| Remidio | 171 | 5.1452% | 0.6661% | 1.2837 |
| Bosch | 17 | 7.7624% | 0.4642% | 1.2068 |
| Forus | 16 | 5.2721% | 0.9102% | 1.3107 |
| Low Disagreement | 76 | 5.5284% | 0.7749% | 1.1542 |
| Medium Disagreement | 75 | 4.5855% | 0.6573% | 1.3147 |
| High Disagreement | 53 | 6.2655% | 0.5317% | 1.4090 |

Disagreement correlates positively with expert-normalized size (Spearman 0.3668) but negatively with absolute region area (-0.4536). These are descriptive associations. There is no device, disagreement-stratum or worst-expert guarantee; Bosch and Forus have small samples.

## Reproduction boundary

The public curve contains summed quantized loss at all 1,001 grid points. It supports exact selection replay, but cannot verify the original images, expert annotations, per-image monotonicity, model training or inference. Warm-up candidate traces and per-image records are not included. Figures and RIGA transfer are planned subsequent additions.

Source: [Chákṣu v2](https://doi.org/10.6084/m9.figshare.20123135.v2). Method: [Conformal Risk Control](https://arxiv.org/abs/2208.02814).
