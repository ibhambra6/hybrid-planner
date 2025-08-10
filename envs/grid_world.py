from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np

from planners.a_star import AStarResult, a_star


@dataclass
class GridWorld:
    width: int
    height: int
    occupancy: np.ndarray  # bool grid, True=obstacle
    start: Tuple[int, int]
    goal: Tuple[int, int]

    @classmethod
    def empty(cls, width: int, height: int) -> "GridWorld":
        occ = np.zeros((width, height), dtype=bool)
        return cls(width=width, height=height, occupancy=occ, start=(0, 0), goal=(width - 1, height - 1))

    def set_obstacles(self, cells: List[Tuple[int, int]]):
        for x, y in cells:
            if 0 <= x < self.width and 0 <= y < self.height:
                self.occupancy[x, y] = True

    def plan_navigate(self, start: Tuple[int, int], goal: Tuple[int, int]) -> Optional[AStarResult]:
        return a_star(self.occupancy, start, goal)


