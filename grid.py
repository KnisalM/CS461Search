from enum import Enum
from typing import Tuple, Union, List
import random


def reconstruct_path(parent, start, goal):
    path = []
    current = goal
    while current is not None:
        path.append(current)
        current = parent.get(current)
    path.reverse()
    return path if path and path[0] == start else None


class CellType(Enum):
    EMPTY = 0
    START = 1
    GOAL = 2
    OBSTACLE = 3


class Cell:
    def __init__(self, row, col):
        self.row = row
        self.col = col
        self.cell_type = CellType.EMPTY


class Grid:
    def __init__(self, size: int):
        self.size = size
        self.cells = [[Cell(i, j) for j in range(size)] for i in range(size)]
        self.start_pos = None
        self.goal_pos = None

    def set_start(self, pos: Tuple[int, int]):
        r, c = pos
        self.cells[r][c].cell_type = CellType.START
        self.start_pos = pos

    def get_start(self) -> Tuple[int, int]:
        return self.start_pos

    def set_goal(self, pos: Tuple[int, int]):
        r, c = pos
        self.cells[r][c].cell_type = CellType.GOAL
        self.goal_pos = pos

    def get_goal(self) -> Tuple[int, int]:
        return self.goal_pos

    def set_obstacles(self, percentage: Union[float, int]) -> None:
        if isinstance(percentage, int):
            percentage = percentage / 100.0
        if not 0.0 <= percentage <= 1.0:
            raise ValueError("Percentage must be between 0 and 1")

        total_cells = self.size * self.size
        target = int(percentage * total_cells)

        eligible_obstacles = []
        for r in range(self.size):
            for c in range(self.size):
                pos = r, c
                if pos == self.start_pos or pos == self.goal_pos:
                    continue
                eligible_obstacles.append(pos)

        if not eligible_obstacles:
            return

        num_obstacles = min(target, len(eligible_obstacles))
        chosen_obstacles = random.sample(eligible_obstacles, num_obstacles)

        for r, c in chosen_obstacles:
            self.cells[r][c].cell_type = CellType.OBSTACLE

    def in_bounds(self, pos: Tuple[int, int]) -> bool:
        r, c = pos
        return 0 <= r < self.size and 0 <= c < self.size

    def get_neighbors(self, pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        r, c = pos
        directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        neighbors = []
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if self.in_bounds((nr, nc)) and self.is_traversable((nr, nc)):
                neighbors.append((nr, nc))

        return neighbors

    def get_cell(self, pos: Tuple[int, int]) -> Cell:
        r, c = pos
        return self.cells[r][c]

    def is_traversable(self, pos: Tuple[int, int]) -> bool:
        r, c = pos
        cell_type = self.cells[r][c].cell_type
        return cell_type in (CellType.EMPTY, CellType.START, CellType.GOAL)

    def get_max_depth(self):
        return self.size * self.size

    def heuristic_method(self, pos1, pos2):
        """Define a heuristic helper function that will be utilized for both greedy best first
    and the A* search functions as the admissible heuristic h(n)"""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    def get_cost(self, cell1, cell2):
        # unweighted will always return 1
        return 1
