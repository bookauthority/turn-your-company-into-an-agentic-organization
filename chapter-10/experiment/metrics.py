from __future__ import annotations

import math
from typing import Iterable


def elapsed_seconds(start: float, end: float) -> float:
    """Return elapsed seconds as a finite float.

    Ensures non-negative, rounded to microseconds for stability.
    """
    value = max(0.0, end - start)
    # Round for reproducibility across platforms
    return round(value, 6)


def mean(values: Iterable[float]) -> float:
    vals = list(values)
    if not vals:
        return math.nan
    return sum(vals) / float(len(vals))
