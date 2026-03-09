import search


from grid import Grid, CellType, reconstruct_path


def test_bfs():
    """Run a series of tests on the BFS algorithm."""
    # ----- Test 1: Simple 3x3 grid, no obstacles -----
    grid1 = Grid(3)
    grid1.set_start((0, 0))
    grid1.set_goal((2, 2))
    start = grid1.get_start()
    goal = grid1.get_goal()
    parent = search.bfs(grid1, start, goal)
    path = reconstruct_path(parent, start, goal)
    # Expected one of the shortest paths of length 4 (Manhattan distance = 4)
    assert path is not None, "Path should exist"
    assert len(path) == 5, f"Path length should be 5 (4 steps), got {len(path)}"
    assert path[0] == start and path[-1] == goal, "Path endpoints incorrect"
    # Check that each step is a valid move (adjacent cardinal)
    for i in range(len(path) - 1):
        r1, c1 = path[i]
        r2, c2 = path[i + 1]
        assert abs(r1 - r2) + abs(c1 - c2) == 1, f"Invalid move from {path[i]} to {path[i + 1]}"
    print("Test 1 passed: simple reachable goal")

    # ----- Test 2: 3x3 grid with a wall forcing detour, unreachable goal -----
    # Let's use a 3x3 grid with obstacles that make the goal unreachable.
    grid2 = Grid(3)
    grid2.set_start((0, 0))
    grid2.set_goal((2, 2))
    # Place obstacles to completely block access: e.g., fill all cells adjacent to start except one that leads to a dead end.
    # Simpler: block (0,1) and (1,0) so start is isolated.
    grid2.cells[0][1].cell_type = CellType.OBSTACLE
    grid2.cells[1][0].cell_type = CellType.OBSTACLE
    # Now start (0,0) has no traversable neighbors, so goal unreachable.
    parent = search.bfs(grid2, (0, 0), (2, 2))
    path = reconstruct_path(parent, (0, 0), (2, 2))
    assert path is None, "Path should not exist when start isolated"
    print("Test 2 passed: unreachable goal")

    print("All BFS tests passed!")


# Run the tests
if __name__ == "__main__":
    test_bfs()
