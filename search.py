from collections import deque


def _validate(grid, start, goal):
    """Extracting the functionality to check if the start and goal locations are in bounds from the functions
    into a helper function to reduce duplicate code"""
    if not grid.in_bounds(start) or not grid.is_traversable(start):
        raise ValueError("Start Position is invalid or not traversable")
    if not grid.in_bounds(goal) or not grid.is_traversable(goal):
        raise ValueError("Goal Position is invalid or not traversable")


def bfs(grid, start, goal):
    _validate(grid, start, goal)

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


def dfs(grid, start, goal):
    _validate(grid, start, goal)

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


def id_dfs(grid, start, goal):
    _validate(grid, start, goal)

    max_depth = grid.size * grid.size

    for depth_limit in range(max_depth + 1):
        parent = {start: None}
        visited = {start}
        # Utilize a stack with format (node, depth)
        stack = [(start, 0)]

        while stack:
            current, depth = stack.pop()
            if current == goal:
                return parent
            if depth < depth_limit:
                for neighbor in grid.get_neighbors(current):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        parent[neighbor] = current
                        stack.append((neighbor, depth + 1))

    return parent


def greedy_best_first(grid, start, goal):
    _validate(grid, start, goal)
