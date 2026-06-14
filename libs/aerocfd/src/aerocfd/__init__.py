"""aerocfd — aircraft CFD post-processing library."""
from aerocfd.models.aircraft import Aircraft
from aerocfd.models.alpha_case import AlphaCase, ConvergenceStatus
from aerocfd.models.dataset import AeroDataset
from aerocfd.models.operating_condition import OperatingCondition
from aerocfd.models.polar import Polar

__all__ = [
    "Aircraft",
    "AlphaCase",
    "ConvergenceStatus",
    "AeroDataset",
    "OperatingCondition",
    "Polar",
]
