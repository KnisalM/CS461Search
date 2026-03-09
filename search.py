from grid import Grid, CellType, Cell
from collections import deque


def bfs(grid, start, goal):
    if not grid.in_bounds(start) or not grid.is_traversable(start):
        raise ValueError("Start Position is invalid or not traversable")
    if not grid.in_bounds(goal) or not grid.is_traversable(goal):
        raise ValueError("Goal Position is invalid or not traversable")

    parent = {start: None}
    visited = {start}
    queue = deque([start])

    while queue:
        current = queue.popleft()

        if current == goal:
            return parent

        for neighbor in grid.get_neighbors(current):
            if neighbor not in visited:
                visited.add(neighbor)
                parent[neighbor] = current
                queue.append(neighbor)

    return parent


def dsf(grid, start, goal):
    if not grid.in_bounds(start) or not grid.is_traversable(start):
        raise ValueError("Start Position is invalid or not traversable")
    if not grid.in_bounds(goal) or not grid.is_traversable(goal):
        raise ValueError("Goal Position is invalid or not traversable")

    parent = {start: None}
    visited = {start}
    stack = [start]

    while stack:
        current = stack.pop()

        if current == goal:
            return parent

        for neighbor in grid.get_neighbors(current):
            if neighbor not in visited:
                visited.add(neighbor)
                parent[neighbor] = current
                stack.append(neighbor)

    return parent
