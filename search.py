from collections import deque
import heapq


def _validate(grid, start, goal):
    """Extracting the functionality to check if the start and goal locations are in bounds from the functions
    into a helper function to reduce duplicate code"""
    if not grid.is_traversable(start):
        raise ValueError("Start Position is invalid or not traversable")
    if not grid.is_traversable(goal):
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

    max_depth = grid.get_max_depth()

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

    parent = {start: None}
    visited = {start}
    # Creating the priority queue heap which will be a min heap with format (heuristic, node)
    pq = [(grid.heuristic_method(start, goal), start)]
    # While loop that continues to loop while PQ is not empty
    while pq:
        _, current = heapq.heappop(pq)
        if current == goal:
            return parent
        for neighbor in grid.get_neighbors(current):
            if neighbor not in visited:
                visited.add(neighbor)
                parent[neighbor] = current
                h = grid.heuristic_method(neighbor, goal)
                heapq.heappush(pq, (h, neighbor))
    return parent


def a_star(grid, start, goal):
    _validate(grid, start, goal)

    parent = {start: None}
    g_score = {start: 0}
    f_score = {start: grid.heuristic_method(start, goal)}
    # A* search will use a priority queue as well, only difference will be in cost so far
    pq = [(grid.heuristic_method(start, goal), start)]
    while pq:
        _, current = heapq.heappop(pq)
        if current == goal:
            return parent
        for neighbor in grid.get_neighbors(current):
            tentative_g = g_score[current] + grid.get_cost(neighbor, goal)
            # Next step is taken if this path to neighbor is better than previously found
            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                parent[neighbor] = current
                g_score[neighbor] = tentative_g
                h = grid.heuristic_method(neighbor, goal)
                f = tentative_g + h
                f_score[neighbor] = f
                heapq.heappush(pq, (f, neighbor))
    return parent


class MetricTracker:
    def __init__(self):
        self.nodes_generated = 0
        self.nodes_expanded = 0
        self.max_frontier_size = 0
        self.neighbors_generated_per_expansion = []  # List of neighbors generated per expansion, used to calculate branching
