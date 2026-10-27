from typing import List, Tuple


def mae(errors: List[float]) -> float:
    if not errors:
        return 0.0
    return sum(abs(e) for e in errors) / len(errors)


def rmse(errors: List[float]) -> float:
    if not errors:
        return 0.0
    mse = sum(e * e for e in errors) / len(errors)
    return mse ** 0.5


def mean_bias(errors: List[float]) -> float:
    if not errors:
        return 0.0
    return sum(errors) / len(errors)


def compute_errors(forecast: List[float], actual: List[float]) -> List[float]:
    # forecast - actual; assume aligned by index/delivery interval
    errors = []
    for f, a in zip(forecast, actual):
        errors.append(f - a)
    return errors
