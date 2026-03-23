import tkinter as tk
from tkinter import ttk, messagebox
from collections import deque
from grid import Grid, CellType
from search import bfs, dfs, id_dfs


class SearchGUI:
    def __init__(self, root):
        self.new_button = None
        self.hover_text = None
        self.hover_rect = None
        self.cell_texts = None
        self.cell_rects = None
        self.tree_canvas = None
        self.start_button = None
        self.size_var = None
        self.alg_var = None
        self.obstacle_var = None
        self.grid_canvas = None
        self.root = root
        self.root.title("Grid Search Visualizer")

        # Default settings
        self.grid_size = 5
        self.cell_size = 60  # pixels per cell
        self.start_pos = None
        self.goal_pos = None
        self.phase = "start"  # "start", "goal", "done"
        self.algorithm = "BFS"
        self.parent = None
        self.visited_cells = set()
        self.obstacles = set()  # store obstacle positions

        # Build UI
        self.create_widgets()
        self.draw_grid()

    def create_widgets(self):
        # Control frame
        control_frame = ttk.Frame(self.root, padding=5)
        control_frame.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(control_frame, text="Grid Size:").grid(row=0, column=0, padx=5)
        self.size_var = tk.StringVar(value="5")
        size_combo = ttk.Combobox(control_frame, textvariable=self.size_var,
                                  values=[str(i) for i in range(5, 21)], width=5)
        size_combo.grid(row=0, column=1, padx=5)
        size_combo.bind("<<ComboboxSelected>>", self.on_size_change)

        ttk.Label(control_frame, text="Algorithm:").grid(row=0, column=2, padx=5)
        self.alg_var = tk.StringVar(value="BFS")
        alg_combo = ttk.Combobox(control_frame, textvariable=self.alg_var,
                                 values=["BFS", "DFS", "IDDFS"], width=5)
        alg_combo.grid(row=0, column=3, padx=5)

        # Obstacle percentage
        ttk.Label(control_frame, text="Obstacles %:").grid(row=0, column=4, padx=5)
        self.obstacle_var = tk.StringVar(value="20")
        obstacle_entry = ttk.Entry(control_frame, textvariable=self.obstacle_var, width=5)
        obstacle_entry.grid(row=0, column=5, padx=5)

        self.start_button = ttk.Button(control_frame, text="Start Search",
                                       command=self.start_search, state=tk.DISABLED)
        self.start_button.grid(row=0, column=6, padx=20)

        # New Search button
        self.new_button = ttk.Button(control_frame, text="New Search",
                                     command=self.new_search)
        self.new_button.grid(row=0, column=7, padx=5)

        # Main display area
        display_frame = ttk.Frame(self.root)
        display_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Left: 2D grid canvas
        self.grid_canvas = tk.Canvas(display_frame, bg="white",
                                     width=self.grid_size * self.cell_size,
                                     height=self.grid_size * self.cell_size)
        self.grid_canvas.pack(side=tk.LEFT, padx=10, pady=10)

        # Right: inverted tree canvas
        self.tree_canvas = tk.Canvas(display_frame, bg="white", width=400, height=400)
        self.tree_canvas.pack(side=tk.RIGHT, padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Bind mouse events for grid
        self.grid_canvas.bind("<Motion>", self.on_grid_motion)
        self.grid_canvas.bind("<Button-1>", self.on_grid_click)
        self.grid_canvas.bind("<Leave>", self.clear_hover)

        # Store cell rectangles and text items
        self.cell_rects = [[None for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        self.cell_texts = [[None for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        self.hover_rect = None
        self.hover_text = None

    def clear_hover(self, event=None):
        """Remove the temporary hover highlight and text."""
        if self.hover_rect:
            self.grid_canvas.delete(self.hover_rect)
            self.hover_rect = None
        if self.hover_text:
            self.grid_canvas.delete(self.hover_text)
            self.hover_text = None

    def draw_grid(self):
        """Draw the grid based on current size and cell states."""
        self.grid_canvas.delete("all")
        self.cell_rects = [[None for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        self.cell_texts = [[None for _ in range(self.grid_size)] for _ in range(self.grid_size)]

        for r in range(self.grid_size):
            for c in range(self.grid_size):
                x1 = c * self.cell_size
                y1 = r * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size
                pos = (r, c)

                # Determine fill color based on cell type
                fill = "white"
                if pos == self.start_pos or pos == self.goal_pos:
                    fill = "black"
                elif pos in self.obstacles:
                    fill = "red"
                elif pos in self.visited_cells:
                    fill = "lightblue"

                rect = self.grid_canvas.create_rectangle(x1, y1, x2, y2,
                                                         fill=fill, outline="gray")
                self.cell_rects[r][c] = rect

                # Draw X for obstacles
                if pos in self.obstacles:
                    # Draw black X
                    self.grid_canvas.create_line(x1, y1, x2, y2, fill="black", width=2)
                    self.grid_canvas.create_line(x1, y2, x2, y1, fill="black", width=2)

                # Draw text for start/goal
                if pos == self.start_pos:
                    text = self.grid_canvas.create_text(x1 + self.cell_size // 2,
                                                        y1 + self.cell_size // 2,
                                                        text="Start", fill="red",
                                                        font=("Arial", 10, "bold"))
                    self.cell_texts[r][c] = text
                elif pos == self.goal_pos:
                    text = self.grid_canvas.create_text(x1 + self.cell_size // 2,
                                                        y1 + self.cell_size // 2,
                                                        text="Goal", fill="green",
                                                        font=("Arial", 10, "bold"))
                    self.cell_texts[r][c] = text

        # Draw path if available (as a thick border)
        if self.parent and self.goal_pos in self.parent:
            path = self.reconstruct_path()
            for (r, c) in path:
                if (r, c) != self.start_pos and (r, c) != self.goal_pos and (r, c) not in self.obstacles:
                    x1 = c * self.cell_size
                    y1 = r * self.cell_size
                    x2 = x1 + self.cell_size
                    y2 = y1 + self.cell_size
                    self.grid_canvas.create_rectangle(x1, y1, x2, y2,
                                                      outline="yellow", width=3)

    def reconstruct_path(self):
        """Reconstruct path from start to goal using parent dict."""
        path = []
        current = self.goal_pos
        while current is not None:
            path.append(current)
            current = self.parent.get(current)
        path.reverse()
        return path if path and path[0] == self.start_pos else []

    def on_grid_motion(self, event):
        """Handle mouse motion: highlight cell if in correct phase."""
        if self.phase not in ("start", "goal"):
            return

        col = event.x // self.cell_size
        row = event.y // self.cell_size
        if not (0 <= row < self.grid_size and 0 <= col < self.grid_size):
            self.clear_hover()
            return

        pos = (row, col)
        # Don't highlight if it's already start/goal or an obstacle (though obstacles aren't set until search)
        if pos == self.start_pos or pos == self.goal_pos:
            self.clear_hover()
            return

        # Remove previous hover highlight
        self.clear_hover()

        # Draw temporary black rectangle
        x1 = col * self.cell_size
        y1 = row * self.cell_size
        x2 = x1 + self.cell_size
        y2 = y1 + self.cell_size
        self.hover_rect = self.grid_canvas.create_rectangle(x1, y1, x2, y2,
                                                            fill="black", outline="gray")

        # Show text based on phase
        text = "Start" if self.phase == "start" else "Goal"
        color = "red" if self.phase == "start" else "green"
        self.hover_text = self.grid_canvas.create_text(x1 + self.cell_size // 2,
                                                       y1 + self.cell_size // 2,
                                                       text=text, fill=color,
                                                       font=("Arial", 10, "bold"))

    def on_grid_click(self, event):
        """Handle click to set start or goal."""
        col = event.x // self.cell_size
        row = event.y // self.cell_size
        if not (0 <= row < self.grid_size and 0 <= col < self.grid_size):
            return

        pos = (row, col)

        if self.phase == "start" and pos != self.goal_pos:
            # Set start
            self.start_pos = pos
            self.phase = "goal"
            self.draw_grid()
        elif self.phase == "goal" and pos != self.start_pos:
            # Set goal
            self.goal_pos = pos
            self.phase = "done"
            self.start_button.config(state=tk.NORMAL)
            self.draw_grid()

        # Remove hover highlight after click
        self.clear_hover()

    def on_size_change(self, event):
        """Change grid size and reset state."""
        new_size = int(self.size_var.get())
        self.grid_size = new_size
        self.start_pos = None
        self.goal_pos = None
        self.phase = "start"
        self.parent = None
        self.visited_cells.clear()
        self.obstacles.clear()
        self.start_button.config(state=tk.DISABLED)

        # Resize canvas
        self.grid_canvas.config(width=self.grid_size * self.cell_size,
                                height=self.grid_size * self.cell_size)
        self.draw_grid()
        self.tree_canvas.delete("all")

    def new_search(self):
        """Reset everything for a new search without changing grid size."""
        self.start_pos = None
        self.goal_pos = None
        self.phase = "start"
        self.parent = None
        self.visited_cells.clear()
        self.obstacles.clear()
        self.start_button.config(state=tk.DISABLED)
        self.draw_grid()
        self.tree_canvas.delete("all")
        self.clear_hover()

    def start_search(self):
        """Run selected search algorithm and visualize results."""
        # Create grid object
        grid = Grid(self.grid_size)
        grid.set_start(self.start_pos)
        grid.set_goal(self.goal_pos)

        # Set obstacles using user-provided percentage
        try:
            obstacle_pct = float(self.obstacle_var.get())
            if obstacle_pct < 0 or obstacle_pct > 100:
                raise ValueError
            grid.set_obstacles(obstacle_pct / 100.0)
        except ValueError:
            messagebox.showerror("Error", "Obstacle percentage must be a number between 0 and 100")
            return

        # Store obstacle positions for display
        self.obstacles.clear()
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                cell = grid.get_cell((r, c))
                if cell.cell_type == CellType.OBSTACLE:
                    self.obstacles.add((r, c))

        # Run search
        algo = self.alg_var.get()
        try:
            if algo == "BFS":
                self.parent = bfs(grid, self.start_pos, self.goal_pos)
            elif algo == "DFS":
                self.parent = dfs(grid, self.start_pos, self.goal_pos)
            elif algo == "IDDFS":
                self.parent = id_dfs(grid, self.start_pos, self.goal_pos)
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return

        # Collect visited cells (all keys in parent plus start)
        self.visited_cells = set(self.parent.keys())
        self.visited_cells.add(self.start_pos)

        # Update grid display
        self.draw_grid()

        # Draw inverted tree
        self.draw_tree(self.parent)

    def draw_tree(self, parent):
        """Draw inverted tree on the right canvas."""
        self.tree_canvas.delete("all")

        if not parent:
            return

        # Build children mapping
        children = {}
        for node, par in parent.items():
            if par is not None:
                children.setdefault(par, []).append(node)

        # BFS to get all nodes and depths
        start = self.start_pos
        depth = {start: 0}
        queue = deque([start])
        nodes_in_order = [start]
        while queue:
            node = queue.popleft()
            for child in children.get(node, []):
                depth[child] = depth[node] + 1
                queue.append(child)
                nodes_in_order.append(child)

        # Assign x coordinates based on BFS order (simple layout)
        x_spacing = 40
        y_spacing = 50
        positions = {}
        for idx, node in enumerate(nodes_in_order):
            x = 50 + idx * x_spacing
            y = 50 + depth[node] * y_spacing
            positions[node] = (x, y)

        # Draw edges
        for node, par in parent.items():
            if par is not None:
                x1, y1 = positions[par]
                x2, y2 = positions[node]
                self.tree_canvas.create_line(x1, y1, x2, y2, fill="black")

        # Draw nodes
        for node, (x, y) in positions.items():
            # Color: start=red, goal=green, others=lightblue
            if node == self.start_pos:
                color = "red"
            elif node == self.goal_pos:
                color = "green"
            else:
                color = "lightblue"
            self.tree_canvas.create_oval(x - 10, y - 10, x + 10, y + 10, fill=color, outline="black")
            # Optionally add text with coordinates
            self.tree_canvas.create_text(x, y, text=f"{node[0]},{node[1]}",
                                         font=("Arial", 8))


if __name__ == "__main__":
    root = tk.Tk()
    app = SearchGUI(root)
    root.mainloop()
