# Preserved bounded CRC reference

`bounded-monotone-expectation-crc-v1.ts` is the unchanged self-contained engine used in the original development research. Its SHA-256 is:

`5cf6ec497d618054dfcb7e41356ec2321f80b36cf50185f07e6ac03a596adfb2`.

The file is preserved for implementation comparison and included in the source distribution. It has no product-service imports. Node's built-in TypeScript stripping runs it through `run_reference.mts`; ordinary Python replay does not require Node.

The engine validates rational losses, candidate endpoints, boundedness and per-unit monotonicity. It sorts the candidate grid and selects the smallest admissible λ using exact BigInt rational arithmetic. Legacy `patient_losses` / `calibration_patient_count` fields mean **images** in the Chákṣu adapter. `ALL_LABELS` maps to the all-Ω spatial endpoint. No patient grouping or guarantee should be inferred from those names.

`scripts/verify_reference.py` constructs synthetic image loss matrices and compares selected λ, certification, fallback and exact rational results to the Python implementation. The package's aggregate API cannot reconstruct per-image validation from published sums.
