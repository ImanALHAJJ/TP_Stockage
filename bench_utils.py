import time
from typing import Callable, Tuple, TypeVar

T = TypeVar("T")

def measure(label: str, fn: Callable[[], T]) -> Tuple[T, float]:
    t0 = time.perf_counter()
    res = fn()
    t1 = time.perf_counter()
    return res, (t1 - t0) * 1000.0
