"""Tier-1 lookup: valid distinct-digit sets for (cage_size, target_sum), plus cage assignment analysis."""
from __future__ import annotations

from functools import lru_cache
from itertools import combinations
from typing import FrozenSet, List, Optional, Sequence, Set, Tuple

MAX_ENUM_SIZE = 6  # larger cages are not enumerated (rare; avoids factorial blow-up)


@lru_cache(maxsize=None)
def partitions(size: int, total: int) -> Tuple[FrozenSet[int], ...]:
    """All sets of `size` distinct digits 1-9 summing to `total`."""
    return tuple(frozenset(c) for c in combinations(range(1, 10), size) if sum(c) == total)


def min_sum(size: int) -> int:
    return size * (size + 1) // 2


def max_sum(size: int) -> int:
    return size * (19 - size) // 2


@lru_cache(maxsize=200_000)
def _analyze(cand_key: Tuple[Tuple[int, ...], ...], target: int):
    n = len(cand_key)
    order = sorted(range(n), key=lambda i: len(cand_key[i]))
    per_cell: List[Set[int]] = [set() for _ in range(n)]
    combos: Set[int] = set()
    chosen = [0] * n

    def dfs(k: int, used: int, remaining: int) -> None:
        left = n - k
        if left == 0:
            if remaining == 0:
                combos.add(used)
                for i in range(n):
                    per_cell[i].add(chosen[i])
            return
        free = [d for d in range(1, 10) if not used >> d & 1]
        if len(free) < left or remaining < sum(free[:left]) or remaining > sum(free[-left:]):
            return
        i = order[k]
        for d in cand_key[i]:
            if used >> d & 1 or d > remaining:
                continue
            chosen[i] = d
            dfs(k + 1, used | (1 << d), remaining - d)

    dfs(0, 0, target)
    sets = tuple(sorted(
        (frozenset(d for d in range(1, 10) if m >> d & 1) for m in combos),
        key=lambda s: sorted(s)))
    return sets, tuple(frozenset(s) for s in per_cell)


def analyze_cage(cell_candidates: Sequence[Set[int]], target: int
                 ) -> Optional[Tuple[Tuple[FrozenSet[int], ...], Tuple[FrozenSet[int], ...]]]:
    """Enumerate every digit assignment consistent with candidates and the sum.

    Returns (valid_digit_sets, per_cell_possible_digits), or None if the cage is too big to enumerate.
    """
    if len(cell_candidates) > MAX_ENUM_SIZE:
        return None
    key = tuple(tuple(sorted(c)) for c in cell_candidates)
    return _analyze(key, target)
