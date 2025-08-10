import numpy as np

from planners.a_star import a_star


def test_a_star_simple():
    grid = np.zeros((10, 10), dtype=bool)
    grid[5, 1:9] = True
    res = a_star(grid, (0, 0), (9, 9))
    assert res is not None
    assert res.path[0] == (0, 0)
    assert res.path[-1] == (9, 9)
    assert res.cost > 0


