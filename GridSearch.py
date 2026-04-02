import tkinter as tk
from tkinter import ttk, messagebox
from collections import deque
from grid import Grid, CellType
from search import bfs, dfs, id_dfs, greedy_best_first, a_star


class SearchGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Grid Search Visualizer - Animated")

        # Grid settings
        self.grid_size = 5
        self.cell_size = 60
        self.start_pos = None
        self.goal_pos = None
        self.phase = "start"          # "start", "goal", "done"
        self.obstacles = set()

        # Animation state
        self.anim_gen = None           # generator from search function (animate=True)
        self.anim_after_id = None
        self.anim_paused = False
        self.anim_speed = 2.0          # cells per second (default 2)
        self.current_node = None       # dark green
        self.frontier_set = set()      # blue
        self.expanded_set = set()      # yellow
        self.anim_parent = {}          # parent dict built during animation
        self.final_parent = None       # parent dict after search completes
        self.final_metrics = None      # metrics dict after search completes

        # Store current grid configuration for restart
        self.current_grid_config = None   # (grid, algorithm_name)

        # Build UI
        self.create_widgets()
        self.draw_grid()

    # ------------------------------------------------------------------
    # UI Creation
    # ------------------------------------------------------------------
    def create_widgets(self):
        # Control frame (top)
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
                                 values=["BFS", "DFS", "IDDFS", "Greedy Best-First", "A*"], width=5)
        alg_combo.grid(row=0, column=3, padx=5)

        ttk.Label(control_frame, text="Obstacles %:").grid(row=0, column=4, padx=5)
        self.obstacle_var = tk.StringVar(value="20")
        obstacle_entry = ttk.Entry(control_frame, textvariable=self.obstacle_var, width=5)
        obstacle_entry.grid(row=0, column=5, padx=5)

        # Start animation button
        self.start_btn = ttk.Button(control_frame, text="Start Search",
                                    command=self.start_animation, state=tk.DISABLED)
        self.start_btn.grid(row=0, column=6, padx=20)

        # New Search button (resets everything)
        self.new_btn = ttk.Button(control_frame, text="New Search", command=self.new_search)
        self.new_btn.grid(row=0, column=7, padx=5)

        # Playback controls frame
        playback_frame = ttk.Frame(self.root, padding=5)
        playback_frame.pack(side=tk.TOP, fill=tk.X)

        self.play_pause_btn = ttk.Button(playback_frame, text="Pause",
                                         command=self.toggle_pause, state=tk.DISABLED)
        self.play_pause_btn.pack(side=tk.LEFT, padx=5)

        self.restart_anim_btn = ttk.Button(playback_frame, text="Restart",
                                           command=self.restart_animation, state=tk.DISABLED)
        self.restart_anim_btn.pack(side=tk.LEFT, padx=5)

        ttk.Label(playback_frame, text="Speed (cells/sec):").pack(side=tk.LEFT, padx=(20, 5))
        self.speed_var = tk.DoubleVar(value=2.0)
        speed_scale = ttk.Scale(playback_frame, from_=0.5, to=5.0, variable=self.speed_var,
                                orient=tk.HORIZONTAL, length=150, command=self.on_speed_change)
        speed_scale.pack(side=tk.LEFT, padx=5)
        self.speed_label = ttk.Label(playback_frame, text="2.0")
        self.speed_label.pack(side=tk.LEFT, padx=5)

        # Main display area (left: grid, right: notebook with tree + metrics)
        main_frame = ttk.Frame(self.root)
        main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Left: grid canvas
        self.grid_canvas = tk.Canvas(main_frame, bg="white",
                                     width=self.grid_size * self.cell_size,
                                     height=self.grid_size * self.cell_size)
        self.grid_canvas.pack(side=tk.LEFT, padx=10, pady=10)

        # Right: notebook (Tree + Metrics)
        right_notebook = ttk.Notebook(main_frame)
        right_notebook.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Tree tab
        tree_frame = ttk.Frame(right_notebook)
        right_notebook.add(tree_frame, text="Search Tree")
        self.tree_canvas = tk.Canvas(tree_frame, bg="white", width=400, height=400)
        v_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree_canvas.yview)
        h_scroll = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.tree_canvas.xview)
        self.tree_canvas.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        self.tree_canvas.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        # Metrics tab
        metrics_frame = ttk.Frame(right_notebook)
        right_notebook.add(metrics_frame, text="Metrics")
        self.metrics_text = tk.Text(metrics_frame, wrap=tk.WORD, height=20, width=40)
        self.metrics_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Bind mouse events for setting start/goal
        self.grid_canvas.bind("<Motion>", self.on_grid_motion)
        self.grid_canvas.bind("<Button-1>", self.on_grid_click)
        self.grid_canvas.bind("<Leave>", self.clear_hover)

        # Store cell references for redrawing
        self.cell_rects = [[None for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        self.cell_texts = [[None for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        self.hover_rect = None
        self.hover_text = None

    # ------------------------------------------------------------------
    # Grid Drawing with Dynamic Colors (Requirement 4)
    # ------------------------------------------------------------------
    def draw_grid(self):
        """Redraw the grid with current colors based on animation state."""
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

                # Determine fill color
                if pos == self.start_pos or pos == self.goal_pos:
                    fill = "black"  # start/goal cells remain black (text overlay will show)
                elif pos in self.obstacles:
                    fill = "red"
                elif pos == self.current_node:
                    fill = "dark green"  # Requirement 3
                elif pos in self.frontier_set:
                    fill = "blue"  # frontier
                elif pos in self.expanded_set:
                    fill = "yellow"  # expanded
                elif self.final_parent and self.goal_pos in self.final_parent:
                    # Show final path in light green after search completes
                    path = self.reconstruct_path(self.final_parent)
                    if pos in path and pos not in (self.start_pos, self.goal_pos):
                        fill = "light green"
                    else:
                        fill = "white"
                else:
                    fill = "white"  # unexplored

                rect = self.grid_canvas.create_rectangle(x1, y1, x2, y2, fill=fill, outline="gray")
                self.cell_rects[r][c] = rect

                # Draw X for obstacles
                if pos in self.obstacles:
                    self.grid_canvas.create_line(x1, y1, x2, y2, fill="black", width=2)
                    self.grid_canvas.create_line(x1, y2, x2, y1, fill="black", width=2)

                # Draw text for start/goal
                if pos == self.start_pos:
                    self.grid_canvas.create_text(x1 + self.cell_size // 2, y1 + self.cell_size // 2,
                                                 text="Start", fill="red", font=("Arial", 10, "bold"))
                elif pos == self.goal_pos:
                    self.grid_canvas.create_text(x1 + self.cell_size // 2, y1 + self.cell_size // 2,
                                                 text="Goal", fill="green", font=("Arial", 10, "bold"))

    def reconstruct_path(self, parent):
        """Reconstruct path from start to goal using given parent dict."""
        if not parent or self.goal_pos not in parent:
            return []
        path = []
        cur = self.goal_pos
        while cur is not None:
            path.append(cur)
            cur = parent.get(cur)
        path.reverse()
        return path if path and path[0] == self.start_pos else []

    # ------------------------------------------------------------------
    # Mouse Handlers for Setting Start/Goal
    # ------------------------------------------------------------------
    def clear_hover(self, event=None):
        if self.hover_rect:
            self.grid_canvas.delete(self.hover_rect)
            self.hover_rect = None
        if self.hover_text:
            self.grid_canvas.delete(self.hover_text)
            self.hover_text = None

    def on_grid_motion(self, event):
        if self.phase not in ("start", "goal"):
            return
        col = event.x // self.cell_size
        row = event.y // self.cell_size
        if not (0 <= row < self.grid_size and 0 <= col < self.grid_size):
            self.clear_hover()
            return
        pos = (row, col)
        if pos == self.start_pos or pos == self.goal_pos:
            self.clear_hover()
            return
        self.clear_hover()
        x1 = col * self.cell_size
        y1 = row * self.cell_size
        x2 = x1 + self.cell_size
        y2 = y1 + self.cell_size
        self.hover_rect = self.grid_canvas.create_rectangle(x1, y1, x2, y2,
                                                            fill="black", outline="gray")
        text = "Start" if self.phase == "start" else "Goal"
        color = "red" if self.phase == "start" else "green"
        self.hover_text = self.grid_canvas.create_text(x1 + self.cell_size // 2,
                                                       y1 + self.cell_size // 2,
                                                       text=text, fill=color,
                                                       font=("Arial", 10, "bold"))

    def on_grid_click(self, event):
        col = event.x // self.cell_size
        row = event.y // self.cell_size
        if not (0 <= row < self.grid_size and 0 <= col < self.grid_size):
            return
        pos = (row, col)
        if self.phase == "start" and pos != self.goal_pos:
            self.start_pos = pos
            self.phase = "goal"
            self.draw_grid()
        elif self.phase == "goal" and pos != self.start_pos:
            self.goal_pos = pos
            self.phase = "done"
            self.start_btn.config(state=tk.NORMAL)
            self.draw_grid()
        self.clear_hover()

    # ------------------------------------------------------------------
    # Animation Control (Requirements 2,3,5,6,7)
    # ------------------------------------------------------------------
    def start_animation(self):
        """Create generator and begin animation."""
        # Build grid with obstacles
        grid = Grid(self.grid_size)
        grid.set_start(self.start_pos)
        grid.set_goal(self.goal_pos)
        try:
            pct = float(self.obstacle_var.get())
            if not 0 <= pct <= 100:
                raise ValueError
            grid.set_obstacles(pct / 100.0)
        except ValueError:
            messagebox.showerror("Error", "Obstacle percentage must be between 0 and 100")
            return

        # Record obstacles for display
        self.obstacles.clear()
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                if grid.get_cell((r, c)).cell_type == CellType.OBSTACLE:
                    self.obstacles.add((r, c))

        # Store the grid configuration for restart
        self.current_grid_config = (grid, self.alg_var.get())

        # Create the generator using the stored config
        self._create_animation_generator()

    def _create_animation_generator(self):
        """Create a new generator from the stored grid configuration."""
        if not self.current_grid_config:
            return
        grid, algo = self.current_grid_config

        try:
            if algo == "BFS":
                gen = bfs(grid, self.start_pos, self.goal_pos, animate=True)
            elif algo == "DFS":
                gen = dfs(grid, self.start_pos, self.goal_pos, animate=True)
            elif algo == "IDDFS":
                gen = id_dfs(grid, self.start_pos, self.goal_pos, animate=True)
            elif algo == "Greedy Best-First":
                gen = greedy_best_first(grid, self.start_pos, self.goal_pos, animate=True)
            elif algo == "A*":
                gen = a_star(grid, self.start_pos, self.goal_pos, animate=True)
            else:
                return
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return

        # Reset animation state
        self.anim_gen = gen
        self.anim_paused = False
        self.current_node = None
        self.frontier_set.clear()
        self.expanded_set.clear()
        self.anim_parent.clear()
        self.final_parent = None
        self.final_metrics = None
        self.play_pause_btn.config(state=tk.NORMAL, text="Pause")
        self.restart_anim_btn.config(state=tk.NORMAL)
        self.start_btn.config(state=tk.DISABLED)
        self.phase = "done"  # prevent further start/goal changes during animation

        # Cancel any pending after call
        if self.anim_after_id:
            self.root.after_cancel(self.anim_after_id)
            self.anim_after_id = None

        # Start stepping
        self._animation_step()

    def _animation_step(self):
        """Advance one step in the generator and schedule next step."""
        if self.anim_paused:
            return

        try:
            # Get next state from generator
            current, frontier, expanded, parent = next(self.anim_gen)
            # Update animation state
            self.current_node = current
            self.frontier_set = frontier
            self.expanded_set = expanded
            self.anim_parent = parent
            # Redraw grid to show changes
            self.draw_grid()
            # Schedule next step based on current speed
            delay_ms = int(1000 / self.anim_speed)
            self.anim_after_id = self.root.after(delay_ms, self._animation_step)
        except StopIteration as e:
            # Generator finished – extract final parent and metrics
            self.final_parent, self.final_metrics = e.value
            self.current_node = None
            self.frontier_set.clear()
            self.expanded_set.clear()
            # Draw final path (light green) and tree
            self.draw_grid()
            self.draw_tree(self.final_parent)
            self.display_metrics(self.final_metrics)  # Requirement 8
            # Disable playback buttons, enable New Search / Start again
            self.play_pause_btn.config(state=tk.DISABLED)
            self.restart_anim_btn.config(state=tk.DISABLED)
            self.start_btn.config(state=tk.NORMAL)
            self.anim_gen = None
            self.anim_after_id = None

    def toggle_pause(self):
        """Pause or resume animation (Requirement 6)."""
        if self.anim_gen is None:
            return
        self.anim_paused = not self.anim_paused
        self.play_pause_btn.config(text="Play" if self.anim_paused else "Pause")
        if self.anim_paused:
            # Cancel any pending after call
            if self.anim_after_id:
                self.root.after_cancel(self.anim_after_id)
                self.anim_after_id = None
        else:
            # Resume: schedule next step if generator not finished
            if self.anim_after_id is None and self.anim_gen is not None:
                self._animation_step()

    def restart_animation(self):
        """Restart the current search visualization from the beginning (Requirement 5)."""
        if self.anim_gen is None and not self.current_grid_config:
            return
        # Cancel current after call
        if self.anim_after_id:
            self.root.after_cancel(self.anim_after_id)
            self.anim_after_id = None
        # Recreate generator using the stored grid configuration (same obstacles)
        self._create_animation_generator()

    def on_speed_change(self, event=None):
        """Update animation speed from slider (Requirement 7)."""
        self.anim_speed = self.speed_var.get()
        self.speed_label.config(text=f"{self.anim_speed:.1f}")
        # The next step will automatically use the new delay

    # ------------------------------------------------------------------
    # Metrics Display (Requirement 8)
    # ------------------------------------------------------------------
    def display_metrics(self, metrics):
        """Show metrics dictionary in the Metrics tab."""
        self.metrics_text.delete(1.0, tk.END)
        if not metrics:
            self.metrics_text.insert(tk.END, "No metrics available.")
            return
        for key, value in metrics.items():
            self.metrics_text.insert(tk.END, f"{key}: {value}\n")

    # ------------------------------------------------------------------
    # Tree Drawing (after search completes)
    # ------------------------------------------------------------------
    def draw_tree(self, parent):
        """Draw inverted tree on the right canvas (same as original)."""
        self.tree_canvas.delete("all")
        if not parent:
            return
        children = {}
        for node, par in parent.items():
            if par is not None:
                children.setdefault(par, []).append(node)
        start = self.start_pos
        depth = {start: 0}
        queue = deque([start])
        nodes_by_depth = {0: [start]}
        while queue:
            node = queue.popleft()
            for child in children.get(node, []):
                depth[child] = depth[node] + 1
                queue.append(child)
                nodes_by_depth.setdefault(depth[child], []).append(child)
        max_depth = max(depth.values()) if depth else 0
        x_spacing = 80
        y_spacing = 60
        start_x = 200
        start_y = 50
        positions = {}
        for d in range(max_depth + 1):
            nodes = nodes_by_depth.get(d, [])
            total = len(nodes)
            for i, node in enumerate(nodes):
                x = start_x + (i - (total - 1) / 2) * x_spacing
                y = start_y + d * y_spacing
                positions[node] = (x, y)
        for node, par in parent.items():
            if par is not None:
                x1, y1 = positions[par]
                x2, y2 = positions[node]
                self.tree_canvas.create_line(x1, y1, x2, y2, fill="black")
        for node, (x, y) in positions.items():
            if node == self.start_pos:
                color = "red"
            elif node == self.goal_pos:
                color = "green"
            else:
                color = "lightblue"
            self.tree_canvas.create_oval(x - 10, y - 10, x + 10, y + 10, fill=color, outline="black")
            self.tree_canvas.create_text(x, y, text=f"{node[0]},{node[1]}", font=("Arial", 8))
        bbox = self.tree_canvas.bbox("all")
        if bbox:
            self.tree_canvas.configure(scrollregion=bbox)

    # ------------------------------------------------------------------
    # Reset Functions (New Search, Size Change)
    # ------------------------------------------------------------------
    def new_search(self):
        """Reset everything for a new search (Requirement 5 also covered)."""
        # Cancel any running animation
        if self.anim_after_id:
            self.root.after_cancel(self.anim_after_id)
            self.anim_after_id = None
        self.start_pos = None
        self.goal_pos = None
        self.phase = "start"
        self.obstacles.clear()
        self.current_node = None
        self.frontier_set.clear()
        self.expanded_set.clear()
        self.anim_parent.clear()
        self.final_parent = None
        self.final_metrics = None
        self.anim_gen = None
        self.anim_paused = False
        self.current_grid_config = None   # clear stored config
        self.start_btn.config(state=tk.DISABLED)
        self.play_pause_btn.config(state=tk.DISABLED)
        self.restart_anim_btn.config(state=tk.DISABLED)
        self.metrics_text.delete(1.0, tk.END)
        self.tree_canvas.delete("all")
        self.draw_grid()

    def on_size_change(self, event):
        """Change grid size and reset everything."""
        self.new_search()  # reuse reset logic
        self.grid_size = int(self.size_var.get())
        self.grid_canvas.config(width=self.grid_size * self.cell_size,
                                height=self.grid_size * self.cell_size)
        self.draw_grid()


if __name__ == "__main__":
    root = tk.Tk()
    app = SearchGUI(root)
    root.mainloop()
