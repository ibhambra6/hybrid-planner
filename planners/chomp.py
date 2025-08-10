from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np
from scipy.ndimage import distance_transform_edt


@dataclass
class CHOMPResult:
    path: np.ndarray  # shape (N, 2)
    cost: float
    converged: bool


def _smoothness_matrix(n_points: int) -> np.ndarray:
    L = np.zeros((n_points, n_points))
    for i in range(n_points):
        if i > 0:
            L[i, i - 1] = -1
        L[i, i] = 2
        if i < n_points - 1:
            L[i, i + 1] = -1
    L[0, 0] = 1
    L[-1, -1] = 1
    return L


def chomp_optimize(
    occupancy: np.ndarray,
    start: Tuple[float, float],
    goal: Tuple[float, float],
    n_points: int = 40,
    step_size: float = 0.1,
    iters: int = 200,
    w_smooth: float = 1.0,
    w_obs: float = 15.0,
) -> Optional[CHOMPResult]:
    """Simplified 2D CHOMP-like optimizer over a distance field.

    - occupancy: bool grid (True=obstacle)
    - path is in grid coordinates (float)
    """
    if occupancy is None or occupancy.ndim != 2:
        return None

    # Distance field: larger is safer; gradient points away from obstacles
    free = ~occupancy
    dist = distance_transform_edt(free)
    gx, gy = np.gradient(dist)

    # Initialize straight-line path
    s = np.array(start, dtype=float)
    g = np.array(goal, dtype=float)
    t = np.linspace(0, 1, n_points)
    path = (1 - t)[:, None] * s[None, :] + t[:, None] * g[None, :]

    L = _smoothness_matrix(n_points)

    def cost_fn(p: np.ndarray) -> float:
        smooth = np.sum(((L @ p) ** 2))
        # Obstacle cost: encourage high distance
        idx = np.clip(np.round(p).astype(int), [0, 0], np.array(dist.shape) - 1)
        d = dist[idx[:, 0], idx[:, 1]] + 1e-6
        obs = np.sum(1.0 / d)
        return w_smooth * smooth + w_obs * obs

    converged = False
    last_cost = cost_fn(path)

    for _ in range(iters):
        # Smoothness gradient
        grad_smooth = 2 * (L.T @ (L @ path))

        # Obstacle gradient from distance field
        idx = np.clip(np.round(path).astype(int), [0, 0], np.array(dist.shape) - 1)
        dg = np.stack([gx[idx[:, 0], idx[:, 1]], gy[idx[:, 0], idx[:, 1]]], axis=1)
        d = dist[idx[:, 0], idx[:, 1]] + 1e-6
        grad_obs = -dg / (d[:, None] ** 2)

        grad = w_smooth * grad_smooth + w_obs * grad_obs

        # Don't move endpoints
        grad[0] = 0
        grad[-1] = 0

        path = path - step_size * grad
        path[:, 0] = np.clip(path[:, 0], 0, dist.shape[0] - 1)
        path[:, 1] = np.clip(path[:, 1], 0, dist.shape[1] - 1)

        cost = cost_fn(path)
        if abs(last_cost - cost) < 1e-4:
            converged = True
            break
        last_cost = cost

    return CHOMPResult(path=path, cost=last_cost, converged=converged)


