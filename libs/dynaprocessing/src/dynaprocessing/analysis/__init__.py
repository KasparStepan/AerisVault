"""Analysis sub-package for dynaprocessing.

Provides filtering, statistical analysis, event detection,
comparison utilities, and derivative calculations.
"""

from dynaprocessing.analysis.filters import (
    apply_butterworth_filter,
    apply_cfc_filter,
    apply_moving_average_filter,
    apply_savgol_filter,
    get_sampling_frequency,
)
from dynaprocessing.analysis.statistics import (
    basic_statistics,
    correlation_matrix,
    frequency_analysis,
    peak_detection,
    settling_time,
    time_window_statistics,
)
from dynaprocessing.analysis.event_detection import (
    auto_detect_events,
    detect_deployment,
    detect_inflation_phases,
    detect_oscillations,
    detect_steady_state,
)
from dynaprocessing.analysis.comparison import (
    align_curves,
    calculate_difference,
    calculate_rmse,
    compare_statistics,
)
from dynaprocessing.analysis.derivatives import (
    first_derivative,
    second_derivative,
)

__all__ = [
    # Filters
    "apply_butterworth_filter",
    "apply_cfc_filter",
    "apply_moving_average_filter",
    "apply_savgol_filter",
    "get_sampling_frequency",
    # Statistics
    "basic_statistics",
    "correlation_matrix",
    "frequency_analysis",
    "peak_detection",
    "settling_time",
    "time_window_statistics",
    # Event detection
    "auto_detect_events",
    "detect_deployment",
    "detect_inflation_phases",
    "detect_oscillations",
    "detect_steady_state",
    # Comparison
    "align_curves",
    "calculate_difference",
    "calculate_rmse",
    "compare_statistics",
    # Derivatives
    "first_derivative",
    "second_derivative",
]
