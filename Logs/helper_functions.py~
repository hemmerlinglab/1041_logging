import math
from typing import Iterable

def ecc(values: Iterable[float]) -> float:
    """
    Extremely light-weight error correction:
    1) If a single number or single-length iterable -> return the number
    2) If length == 2 -> return mean
    3) If length >= 3 -> drop min and max, then mean
    4) If empty -> return NaN
    """

    # Normalize to list
    if isinstance(values, (int, float)):
        return float(values)

    vals = list(values)
    n = len(vals)
    if n == 0:
        return math.nan
    if n == 1:
        return float(vals[0])
    if n == 2:
        return (float(vals[0]) + float(vals[1])) / 2.0

    vals.sort()
    core = vals[1:-1]
    return sum(core) / len(core) if core else (sum(vals) / len(vals))

