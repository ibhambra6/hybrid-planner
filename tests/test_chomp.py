import numpy as np

from planners.chomp import chomp_optimize


def test_chomp_runs():
    occ = np.zeros((50, 50), dtype=bool)
    occ[20:30, 20:30] = True
    res = chomp_optimize(occ, (5, 5), (45, 45), n_points=30, iters=50)
    assert res is not None
    assert res.path.shape[0] == 30


