import random
from typing import Any


class DeterministicRandom:
    """Wrapper around random.Random for deterministic behavior.

    This makes it easy to evolve the experiment while keeping a clear
    seeded RNG per simulator instance.
    """

    def __init__(self, seed: int) -> None:
        self._rng = random.Random(seed)

    def choice(self, seq: list[Any]) -> Any:
        return self._rng.choice(seq)

    def randint(self, a: int, b: int) -> int:
        return self._rng.randint(a, b)

    def uniform(self, a: float, b: float) -> float:
        return self._rng.uniform(a, b)

    def random(self) -> float:
        return self._rng.random()

    def shuffle(self, x: list[Any]) -> None:
        self._rng.shuffle(x)
