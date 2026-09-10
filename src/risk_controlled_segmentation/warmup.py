"""Regenerate descriptive warm-up summaries using linear (R type 7) quantiles."""
import math
from statistics import fmean, pstdev

# Output path, projected per-run field, whether the historical summary includes width.
METRICS = (
    ("lambda", "lambda", True),
    ("calibration.total_q_loss_mass", "calibration_total_loss", False),
    ("calibration.empirical_q_risk", "calibration_quantized", False),
    ("calibration.adjusted_r_plus_q", "calibration_adjusted", False),
    ("calibration.raw_omission", "calibration_raw", False),
    ("calibration.quantization_gap", "calibration_gap", False),
    ("evaluation.raw_omission", "evaluation_raw", True),
    ("evaluation.quantized_omission", "evaluation_quantized", True),
    ("evaluation.quantization_gap", "evaluation_gap", False),
    ("spatial_utility.mean_region_area_fraction", "mean_area", True),
    ("spatial_utility.median_image_area_fraction", "median_area", False),
    ("spatial_utility.mean_normalized_region_size", "normalized_size", True),
    ("spatial_utility.all_omega_rate", "all_omega_rate", True),
    ("worst_expert.mean_omission", "worst_expert", False),
    ("worst_expert.all_five_95_covered_rate", "all_five_95_rate", True),
    ("disagreement.rho_d_vs_normalized_size", "disagreement_rho", True),
    ("disagreement.high_minus_low_mean_normalized_size", "disagreement_high_minus_low", False),
)
WIDTHS = {
    "lambda": "lambda",
    "raw_evaluation_omission": "evaluation.raw_omission",
    "quantized_evaluation_omission": "evaluation.quantized_omission",
    "mean_region_area_fraction": "spatial_utility.mean_region_area_fraction",
    "mean_normalized_region_size": "spatial_utility.mean_normalized_region_size",
    "all_omega_rate": "spatial_utility.all_omega_rate",
    "all_five_95_covered_rate": "worst_expert.all_five_95_covered_rate",
    "rho_d_vs_normalized_size": "disagreement.rho_d_vs_normalized_size",
}


def get(value, path):
    for key in path.split("."):
        value = value[key]
    return value


def put(value, path, item):
    *parents, key = path.split(".")
    for parent in parents:
        value = value.setdefault(parent, {})
    value[key] = item


def percentile(values, probability):
    if not values or not 0 <= probability <= 1 or not all(math.isfinite(x) for x in values):
        raise ValueError("Quantiles require nonempty finite values and probability in [0, 1]")
    values = sorted(values)
    position = (len(values) - 1) * probability
    lo = math.floor(position)
    hi = math.ceil(position)
    return values[lo] + (values[hi] - values[lo]) * (position - lo)


def distribution(values):
    values = list(values)
    if not values or not all(type(x) in (int, float) and math.isfinite(x) for x in values):
        raise ValueError("Distribution requires nonempty finite numbers")
    return {"min": min(values), "p05": percentile(values, .05), "p25": percentile(values, .25),
            "median": percentile(values, .5), "mean": fmean(values), "p75": percentile(values, .75),
            "p95": percentile(values, .95), "max": max(values), "standard_deviation": pstdev(values)}


def summarize_warmup(runs):
    curve = []
    for n in sorted({row["n"] for row in runs}):
        rows = [row for row in runs if row["n"] == n]
        count = len(rows)
        certified = sum(row["certified"] for row in rows)
        nontrivial = sum(row["utility"] == "NONTRIVIAL" for row in rows)
        result = {
            "n": n, "replicate_count": count,
            "formal": {"certified_count": certified, "certification_rate": certified / count,
                       "fallback_count": sum(row["fallback"] != "NONE" for row in rows)},
            "non_vacuity": {"nontrivial_spatial_certified_count": nontrivial, "nontrivial_rate": nontrivial / count,
                            "fully_spatially_vacuous_count": sum(row["utility"] == "ALL_OMEGA_CERTIFIED" for row in rows)},
        }
        for target, field, width in METRICS:
            valid = [row[field] for row in rows if row[field] is not None]
            stats = distribution(valid)
            if width:
                stats["p05_p95_width"] = stats["p95"] - stats["p05"]
            if field == "disagreement_rho":
                stats.update(valid_count=len(valid), null_count=count - len(valid))
            put(result, target, stats)
        curve.append(result)
    repeated = [row for row in curve if row["replicate_count"] > 1]
    if len(repeated) < 2:
        raise ValueError("At least two repeated tiers required for this study's stability analysis")
    by_n = [{"n": row["n"], **{name: get(row, path)["p05_p95_width"] for name, path in WIDTHS.items()}}
            for row in repeated]
    start, end = by_n[0], by_n[-1]
    reductions = {key: None if start[key] == 0 else (start[key] - end[key]) / start[key] for key in WIDTHS}
    assessed = sum(start[key] > 0 for key in WIDTHS)
    improved = sum(start[key] > 0 and end[key] < start[key] for key in WIDTHS)
    first = lambda rows, predicate: next((row["n"] for row in rows if predicate(row)), "NOT_OBSERVED")
    milestones = {
        "first_n_any_formal": first(curve, lambda row: row["formal"]["certified_count"] > 0),
        "first_n_any_nontrivial_spatial": first(curve, lambda row: row["non_vacuity"]["nontrivial_spatial_certified_count"] > 0),
    }
    for percent in (50, 90):
        milestones[f"first_n_formal_at_least_{percent}_percent"] = first(curve, lambda row: row["formal"]["certification_rate"] >= percent / 100)
        milestones[f"first_n_nontrivial_at_least_{percent}_percent"] = first(curve, lambda row: row["non_vacuity"]["nontrivial_rate"] >= percent / 100)
    for limit in (.25, .10, .05, .025):
        milestones[f"first_n_median_mean_area_at_or_below_{str(limit).replace('.', '_')}"] = first(curve, lambda row: row["spatial_utility"]["mean_region_area_fraction"]["median"] <= limit)
    for limit in (.20, .10, .05, .02):
        milestones[f"first_n_lambda_width_below_{str(limit).replace('.', '_')}"] = first(repeated, lambda row: row["lambda"]["p05_p95_width"] < limit)
    return {"curve": curve, "milestones": milestones,
            "stability": {"by_n": by_n, "relative_reduction_n20_to_n200": reductions,
                          "dimensions_assessed": assessed, "dimensions_with_narrower_width": improved}}
