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


def test_dfs():
    # ----- Test 1: Simple 3x3 grid, no obstacles -----
    grid1 = Grid(3)
    grid1.set_start((0, 0))
    grid1.set_goal((2, 2))
    start = grid1.get_start()
    goal = grid1.get_goal()
    parent = search.dfs(grid1, start, goal)
    path = reconstruct_path(parent, start, goal)
    assert path is not None, "Path should exist"
    assert path[0] == start and path[-1] == goal, "Path endpoints incorrect"
    # Check that each step is a valid cardinal move and not an obstacle
    for i in range(len(path) - 1):
        r1, c1 = path[i]
        r2, c2 = path[i + 1]
        assert abs(r1 - r2) + abs(c1 - c2) == 1, f"Invalid move from {path[i]} to {path[i + 1]}"
        # Ensure the cell is traversable (it should be, since path is built from parent map)
        cell_type = grid1.get_cell(path[i + 1]).cell_type
        assert cell_type != CellType.OBSTACLE, f"Path includes obstacle at {path[i + 1]}"
    print("Test 1 passed: simple reachable goal")

    # ----- Test 2: Grid with obstacles that still allow a path -----
    grid2 = Grid(3)
    grid2.set_start((0, 0))
    grid2.set_goal((2, 2))
    # Place an obstacle at (1,1) – this blocks the direct diagonal but a path still exists
    grid2.cells[1][1].cell_type = CellType.OBSTACLE
    # Also block (0,1) to force a specific route? Not necessary, just ensure at least one path exists.
    # For reliability, we'll leave (0,1) and (1,0) open.
    parent = search.dfs(grid2, (0, 0), (2, 2))
    path = reconstruct_path(parent, (0, 0), (2, 2))
    assert path is not None, "Path should exist despite obstacle"
    assert path[0] == (0, 0) and path[-1] == (2, 2), "Path endpoints incorrect"
    # Verify the path does not pass through the obstacle
    for pos in path:
        assert grid2.get_cell(pos).cell_type != CellType.OBSTACLE, f"Path includes obstacle at {pos}"
    print("Test 2 passed: path around obstacle")

    # ----- Test 3: Unreachable goal (start isolated by obstacles) -----
    grid3 = Grid(3)
    grid3.set_start((0, 0))
    grid3.set_goal((2, 2))
    # Block all neighbors of start
    grid3.cells[0][1].cell_type = CellType.OBSTACLE
    grid3.cells[1][0].cell_type = CellType.OBSTACLE
    # Start (0,0) now has no traversable neighbors
    parent = search.dfs(grid3, (0, 0), (2, 2))
    path = reconstruct_path(parent, (0, 0), (2, 2))
    assert path is None, "Path should not exist when start isolated"
    print("Test 3 passed: unreachable goal")

    print("All DFS tests passed!")

# Run the tests
if __name__ == "__main__":
    test_bfs()
    test_dfs()
