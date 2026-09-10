"""Bounded monotone expectation CRC on a complete, fixed rational grid.

Aggregate validation cannot establish per-image monotonicity or exchangeability.
Use aggregate_image_losses for per-image structural checks before aggregation.
"""
from dataclasses import dataclass
from fractions import Fraction
from typing import Sequence

METHOD = "BOUNDED_MONOTONE_EXPECTATION_CRC_V1"
QUANTIZATION = 10_000


def integer(value: int, label: str, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise ValueError(f"{label} must be an integer >= {minimum}")
    return value


def exact(value: str | Fraction | int) -> Fraction:
    if isinstance(value, bool) or not isinstance(value, (str, Fraction, int)):
        raise ValueError("Use a rational string, integer or Fraction; floats are not exact inputs")
    try:
        return Fraction(value)
    except (ValueError, ZeroDivisionError) as error:
        raise ValueError("Invalid exact rational") from error


def rational_text(value: Fraction) -> str:
    return f"{value.numerator}/{value.denominator}"


def quantized_omission(missed: int, area: int) -> Fraction:
    integer(missed, "missed")
    integer(area, "area", 1)
    if missed > area:
        raise ValueError("missed exceeds reference area")
    return Fraction((QUANTIZATION * missed + area - 1) // area, QUANTIZATION)


def image_omission(counts: Sequence[tuple[int, int]], *, expected_experts: int) -> tuple[Fraction, Fraction]:
    """Equal expert average for ONE image; returns raw and upward-quantized loss."""
    integer(expected_experts, "expected_experts", 1)
    if len(counts) != expected_experts:
        raise ValueError("Expert panel size mismatch")
    quantized = [quantized_omission(missed, area) for missed, area in counts]
    raw = [Fraction(missed, area) for missed, area in counts]
    return sum(raw, Fraction()) / expected_experts, sum(quantized, Fraction()) / expected_experts


def validate_curve(values: Sequence[int], *, maximum: int, grid_denominator: int) -> None:
    integer(grid_denominator, "grid_denominator", 1)
    if len(values) != grid_denominator + 1:
        raise ValueError("Curve must include every grid point, including 0 and 1")
    for value in values:
        integer(value, "loss numerator")
        if value > maximum:
            raise ValueError("Loss exceeds its bounded maximum")
    if any(a < b for a, b in zip(values, values[1:])):
        raise ValueError("Loss must be non-increasing along the grid")
    if values[-1] != 0:
        raise ValueError("All-Omega endpoint must have zero omission")


def aggregate_image_losses(image_numerators: Sequence[Sequence[int]], *, loss_denominator: int,
                           grid_denominator: int = 1000) -> tuple[int, ...]:
    integer(loss_denominator, "loss_denominator", 1)
    if not image_numerators:
        raise ValueError("Empty calibration image population")
    for curve in image_numerators:
        validate_curve(curve, maximum=loss_denominator, grid_denominator=grid_denominator)
    return tuple(sum(column) for column in zip(*image_numerators, strict=True))


@dataclass(frozen=True)
class Calibration:
    n_images: int
    grid_denominator: int
    alpha: Fraction
    lambda_index: int
    certified: bool
    total_loss: Fraction

    def as_dict(self) -> dict:
        return {
            "method": METHOD, "n_images": self.n_images, "candidate_count": self.grid_denominator + 1,
            "alpha": rational_text(self.alpha), "lambda_index": self.lambda_index,
            "lambda": rational_text(Fraction(self.lambda_index, self.grid_denominator)),
            "certified": self.certified, "fallback": "NONE" if self.certified else "ALL_OMEGA",
            "total_loss": rational_text(self.total_loss),
            "empirical_risk": rational_text(self.total_loss / self.n_images),
            "adjusted_risk": rational_text((self.total_loss + 1) / (self.n_images + 1)),
        }


def calibrate_aggregate(totals: Sequence[int], *, loss_denominator: int, n_images: int,
                        alpha: str | Fraction, grid_denominator: int = 1000) -> Calibration:
    """Replay aggregate sufficient statistics; all comparisons use integer arithmetic.

    certified records whether the finite-sample inequality was satisfied. The
    expectation guarantee requires the study assumptions; it is not a PAC bound.
    """
    integer(loss_denominator, "loss_denominator", 1)
    integer(n_images, "n_images", 1)
    budget = exact(alpha)
    if not 0 < budget < 1:
        raise ValueError("alpha must be strictly between 0 and 1")
    validate_curve(totals, maximum=n_images * loss_denominator, grid_denominator=grid_denominator)
    for index, total in enumerate(totals):
        # (total / D + 1) / (n + 1) <= a/b, without binary rounding.
        if (total + loss_denominator) * budget.denominator <= budget.numerator * loss_denominator * (n_images + 1):
            return Calibration(n_images, grid_denominator, budget, index, True, Fraction(total, loss_denominator))
    return Calibration(n_images, grid_denominator, budget, grid_denominator, False, Fraction(0))


def nested_region(scores: Sequence[Fraction], valid: Sequence[bool], *, lambda_value: Fraction) -> tuple[bool, ...]:
    """Small exact-score example; this is not the historical float32 raster decoder."""
    lam = exact(lambda_value)
    if not 0 <= lam <= 1 or len(scores) != len(valid) or not scores or not any(valid):
        raise ValueError("Invalid region inputs")
    if any(type(value) is not bool for value in valid):
        raise ValueError("valid must contain booleans")
    values = [exact(score) for score in scores]
    if any(not 0 <= score <= 1 for score in values):
        raise ValueError("Scores must lie in [0, 1]")
    return tuple(inside and score >= 1 - lam for score, inside in zip(values, valid))
