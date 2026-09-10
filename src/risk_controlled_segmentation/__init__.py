"""Exact bounded omission-risk calibration; aggregate retinal evidence replay."""
from .method import calibrate_aggregate, aggregate_image_losses, image_omission, quantized_omission

__all__ = ["calibrate_aggregate", "aggregate_image_losses", "image_omission", "quantized_omission"]
__version__ = "0.1.0.dev0"
