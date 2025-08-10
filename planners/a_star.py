from __future__ import annotations

from dataclasses import dataclass
from heapq import heappop, heappush
from typing import Iterable, List, Optional, Tuple

import numpy as np


Grid = np.ndarray  # dtype=bool (True = obstacle)


@dataclass
class AStarResult:
    path: List[Tuple[int, int]]
    cost: float
    expanded: int


def manhattan(a: Tuple[int, int], b: Tuple[int, int]) -> float:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def neighbors(pos: Tuple[int, int], grid: Grid) -> Iterable[Tuple[int, int]]:
    x, y = pos
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nx, ny = x + dx, y + dy
        if 0 <= nx < grid.shape[0] and 0 <= ny < grid.shape[1]:
            if not grid[nx, ny]:
                yield (nx, ny)


def reconstruct(came_from: dict, current: Tuple[int, int]) -> List[Tuple[int, int]]:
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    path.reverse()
    return path


def a_star(grid: Grid, start: Tuple[int, int], goal: Tuple[int, int]) -> Optional[AStarResult]:
    if grid[start] or grid[goal]:
        return None
    open_set: List[Tuple[float, Tuple[int, int]]] = []
    heappush(open_set, (0.0, start))
    came_from: dict = {}

    g_score = {start: 0.0}
    f_score = {start: manhattan(start, goal)}
    expanded = 0

    while open_set:
        _, current = heappop(open_set)
        expanded += 1
        if current == goal:
            path = reconstruct(came_from, current)
            return AStarResult(path=path, cost=g_score[current], expanded=expanded)

        for nb in neighbors(current, grid):
            tentative_g = g_score[current] + 1.0
            if tentative_g < g_score.get(nb, float("inf")):
                came_from[nb] = current
                g_score[nb] = tentative_g
                f_score[nb] = tentative_g + manhattan(nb, goal)
                heappush(open_set, (f_score[nb], nb))

    return None


