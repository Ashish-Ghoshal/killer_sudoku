"""Generate a uniquely solvable killer puzzle (for examples/tests). Usage: python -m tools.generate_puzzle SEED"""
from __future__ import annotations

import json
import random
import sys

from engine.validator import count_solutions
from models.board import Cage, cell_name


def random_solution(rng: random.Random):
    base = [[(3 * (r % 3) + r // 3 + c) % 9 + 1 for c in range(9)] for r in range(9)]
    digits = list(range(1, 10)); rng.shuffle(digits)
    bands = [b * 3 + i for b in rng.sample(range(3), 3) for i in rng.sample(range(3), 3)]
    stacks = [s * 3 + i for s in rng.sample(range(3), 3) for i in rng.sample(range(3), 3)]
    return [[digits[base[bands[r]][stacks[c]] - 1] - 1 + 1 for c in range(9)] for r in range(9)]


def neighbors(cell):
    r, c = cell
    return [(r + dr, c + dc) for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)) if 0 <= r + dr < 9 and 0 <= c + dc < 9]


def make_groups(sol, rng, sizes=(2, 2, 3, 3, 3, 4)):
    free = {(r, c) for r in range(9) for c in range(9)}
    groups = []
    order = [(r, c) for r in range(9) for c in range(9)]
    rng.shuffle(order)
    for start in order:
        if start not in free:
            continue
        group, want = [start], rng.choice(sizes)
        free.discard(start)
        while len(group) < want:
            opts = [n for g in group for n in neighbors(g) if n in free and sol[n[0]][n[1]] not in {sol[a][b] for a, b in group}]
            if not opts:
                break
            nxt = rng.choice(opts)
            group.append(nxt); free.discard(nxt)
        groups.append(group)
    return groups


def components(cells):
    cells, comps = set(cells), []
    while cells:
        stack, comp = [cells.pop()], []
        while stack:
            cur = stack.pop(); comp.append(cur)
            for n in neighbors(cur):
                if n in cells:
                    cells.discard(n); stack.append(n)
        comps.append(sorted(comp))
    return comps


def to_cages(groups, sol):
    return [Cage(i + 1, sum(sol[r][c] for r, c in g), tuple(g)) for i, g in enumerate(groups)]


def generate(seed: int):
    rng = random.Random(seed)
    sol = random_solution(rng)
    groups = [sorted(g) for g in make_groups(sol, rng)]
    while True:
        cages = to_cages(groups, sol)
        found = count_solutions(cages, 2)
        if len(found) == 1:
            return cages, sol
        other = next(f for f in found if f != sol)
        diff = next((r, c) for r in range(9) for c in range(9) if other[r][c] != sol[r][c])
        g = next(g for g in groups if diff in g)
        groups.remove(g)
        groups.append([diff])  # reveal that cell as a given (1-cell cage)
        rest = [c for c in g if c != diff]
        groups.extend(components(rest))


if __name__ == "__main__":
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    cages, sol = generate(seed)
    print(json.dumps({"name": f"generated-{seed}", "cages": [
        {"sum": c.target_sum, "cells": [cell_name(x) for x in c.cells]} for c in cages], "solution": sol}))
