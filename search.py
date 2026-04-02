import time
from collections import deque
import heapq


def _validate(grid, start, goal):
    """Extracting the functionality to check if the start and goal locations are in bounds from the functions
    into a helper function to reduce duplicate code"""
    if not grid.is_traversable(start):
        raise ValueError("Start Position is invalid or not traversable")
    if not grid.is_traversable(goal):
        raise ValueError("Goal Position is invalid or not traversable")


def bfs(grid, start, goal, animate=False):
    _validate(grid, start, goal)
    start_time = time.perf_counter()
    tracker = MetricTracker()
    parent = {start: None}
    visited = {start}
    queue = deque([start])
    tracker.generate(1)

    if animate:
        frontier_set = set(queue)
        expanded_set = set()

    while queue:
        current = queue.popleft()
        gen_count = 0
        if animate:
            frontier_set.discard(current)
            expanded_set.add(current)
            yield current, frontier_set.copy(), expanded_set.copy(), parent.copy()
        if current == goal:
            break

        for neighbor in grid.get_neighbors(current):
            if neighbor not in visited:
                visited.add(neighbor)
                parent[neighbor] = current
                queue.append(neighbor)
                if animate:
                    frontier_set.add(neighbor)
                tracker.generate(1)
                gen_count += 1
        tracker.expand(len(queue), gen_count)

    runtime = time.perf_counter() - start_time

    # compute depth and cost of search, doing within search algorithms because otherwise MetricTracker needs access to grid/adjacency graph classes, no need for that access
    if goal in parent:
        depth = 0
        node = goal
        while parent[node] is not None:
            depth += 1
            node = parent[node]
        cost = grid.calculate_path_cost(parent,goal)
    else:
        depth = -1
        cost = float('inf')

    tracker.branching()
    metrics = tracker.get_metrics(depth, cost, runtime)
    if animate:
        return parent, metrics
    return parent, metrics


def dfs(grid, start, goal):
    _validate(grid, start, goal)
    start_time = time.perf_counter()
    tracker = MetricTracker()
    parent = {start: None}
    visited = {start}
    stack = [start]
    tracker.generate(1)

    while stack:
        current = stack.pop()
        gen_count = 0

        if current == goal:
            break

        for neighbor in grid.get_neighbors(current):
            if neighbor not in visited:
                visited.add(neighbor)
                parent[neighbor] = current
                stack.append(neighbor)
                tracker.generate(1)
                gen_count += 1
        tracker.expand(len(stack), gen_count)

    runtime = time.perf_counter() - start_time

    # compute depth and cost of search, doing within search algorithms because otherwise MetricTracker needs access to grid/adjacency graph classes, no need for that access
    if goal in parent:
        depth = 0
        node = goal
        while parent[node] is not None:
            depth += 1
            node = parent[node]
        cost = grid.calculate_path_cost(parent,goal)
    else:
        depth = -1
        cost = float('inf')

    tracker.branching()
    metrics = tracker.get_metrics(depth, cost, runtime)
    return parent, metrics


def id_dfs(grid, start, goal):
    _validate(grid, start, goal)
    start_time = time.perf_counter()
    tracker = MetricTracker()
    max_depth = grid.get_max_depth()
    tracker.generate(1)

    for depth_limit in range(max_depth + 1):
        parent = {start: None}
        visited = {start}
        # Utilize a stack with format (node, depth)
        stack = [(start, 0)]

        while stack:
            current, depth = stack.pop()
            gen_count = 0
            if current == goal:
                break
            if depth < depth_limit:
                for neighbor in grid.get_neighbors(current):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        parent[neighbor] = current
                        stack.append((neighbor, depth + 1))
                        tracker.generate(1)
                        gen_count += 1
                tracker.expand(len(stack), gen_count)

    runtime = time.perf_counter() - start_time

    # compute depth and cost of search, doing within search algorithms because otherwise MetricTracker needs access to grid/adjacency graph classes, no need for that access
    if goal in parent:
        depth = 0
        node = goal
        while parent[node] is not None:
            depth += 1
            node = parent[node]
        cost = grid.calculate_path_cost(parent,goal)
    else:
        depth = -1
        cost = float('inf')

    tracker.branching()
    metrics = tracker.get_metrics(depth, cost, runtime)
    return parent, metrics


def greedy_best_first(grid, start, goal):
    _validate(grid, start, goal)
    start_time = time.perf_counter()
    tracker = MetricTracker()
    parent = {start: None}
    visited = {start}
    # Creating the priority queue heap which will be a min heap with format (heuristic, node)
    pq = [(grid.heuristic_method(start, goal), start)]
    tracker.generate(1)
    # While loop that continues to loop while PQ is not empty
    while pq:
        _, current = heapq.heappop(pq)
        gen_count = 0
        if current == goal:
            break
        for neighbor in grid.get_neighbors(current):
            if neighbor not in visited:
                visited.add(neighbor)
                parent[neighbor] = current
                h = grid.heuristic_method(neighbor, goal)
                heapq.heappush(pq, (h, neighbor))
                tracker.generate(1)
                gen_count += 1
        tracker.expand(len(pq), gen_count)
    runtime = time.perf_counter() - start_time

    # compute depth and cost of search, doing within search algorithms because otherwise MetricTracker needs access to grid/adjacency graph classes, no need for that access
    if goal in parent:
        depth = 0
        node = goal
        while parent[node] is not None:
            depth += 1
            node = parent[node]
        cost = grid.calculate_path_cost(parent,goal)
    else:
        depth = -1
        cost = float('inf')

    tracker.branching()
    metrics = tracker.get_metrics(depth, cost, runtime)
    return parent, metrics


def a_star(grid, start, goal):
    _validate(grid, start, goal)
    start_time = time.perf_counter()
    tracker = MetricTracker()
    parent = {start: None}
    g_score = {start: 0}
    f_score = {start: grid.heuristic_method(start, goal)}
    # A* search will use a priority queue as well, only difference will be in cost so far
    pq = [(grid.heuristic_method(start, goal), start)]
    tracker.generate(1)
    while pq:
        _, current = heapq.heappop(pq)
        gen_count=0
        if current == goal:
            break
        for neighbor in grid.get_neighbors(current):
            tentative_g = g_score[current] + grid.get_cost(current, neighbor)
            # Next step is taken if this path to neighbor is better than previously found
            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                parent[neighbor] = current
                g_score[neighbor] = tentative_g
                h = grid.heuristic_method(neighbor, goal)
                f = tentative_g + h
                f_score[neighbor] = f
                heapq.heappush(pq, (f, neighbor))
                tracker.generate(1)
                gen_count += 1
        tracker.expand(len(pq), gen_count)
    runtime = time.perf_counter() - start_time

    # compute depth and cost of search, doing within search algorithms because otherwise MetricTracker needs access to grid/adjacency graph classes, no need for that access
    if goal in parent:
        depth = 0
        node = goal
        while parent[node] is not None:
            depth += 1
            node = parent[node]
        cost = grid.calculate_path_cost(parent,goal)
    else:
        depth = -1
        cost = float('inf')

    tracker.branching()
    metrics = tracker.get_metrics(depth, cost, runtime)
    return parent, metrics


class MetricTracker:
    def __init__(self):
        self.nodes_generated = 0
        self.nodes_expanded = 0
        self.max_frontier_size = 0
        self.neighbors_generated_per_expansion = []  # List of neighbors generated per expansion, used to calculate branching
        self.average_branching = 0
        self.max_branching = 0

    def generate(self, count=1):
        self.nodes_generated += count

    def expand(self, frontier: int, neighbors_generated: int):
        self.nodes_expanded += 1
        self.max_frontier_size = max(self.max_frontier_size, frontier)
        self.neighbors_generated_per_expansion.append(neighbors_generated)

    def branching(self):
        if self.neighbors_generated_per_expansion:
            self.average_branching = (
                        sum(self.neighbors_generated_per_expansion) / len(self.neighbors_generated_per_expansion))
            self.max_branching = max(self.neighbors_generated_per_expansion)
        else:
            self.average_branching = 0
            self.max_branching = 0

    def get_metrics(self, depth, cost, runtime):
        """To calculate cost within the metric tracker, it would need to have cross access to the grid or adjacencygraph objects
        Since this cross referencing could cause issues, we will instead pass depth, cost, and runtime from the search algorithm
        """
        return {
            'runtime': runtime,
            'Peak Frontier Size': self.max_frontier_size,
            'Nodes Generated': self.nodes_generated,
            'Nodes Expanded': self.nodes_expanded,
            'Average Branching Factor': self.average_branching,
            'Max Branching Factor': self.max_branching,
            'Solution Depth': depth,
            'Path Cost': cost
        }
