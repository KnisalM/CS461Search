import tkinter as tk
from tkinter import ttk, messagebox
import random
import math
from adjacency_graph import AdjacencyGraph
from search import bfs, dfs, id_dfs, greedy_best_first, a_star


class AdjacencyGraphSearchGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Adjacency Graph Search Visualizer")

        # Graph and animation state
        self.graph = None
        self.node_positions = {}
        self.node_circles = {}
        self.node_texts = {}
        self.edge_lines = []
        self.start_node = None
        self.goal_node = None
        self.phase = "start"

        # Animation state
        self.anim_gen = None
        self.anim_after_id = None
        self.anim_paused = False
        self.anim_speed = 2.0
        self.current_node = None
        self.frontier_set = set()
        self.expanded_set = set()
        self.anim_parent = {}
        self.final_parent = None
        self.final_metrics = None
        self.current_grid_config = None

        # Canvas size
        self.canvas_width = 1200
        self.canvas_height = 900
        self.node_radius = 18
        self.font_size = 8

        # UI elements
        self.create_widgets()
        self.canvas.config(width=self.canvas_width, height=self.canvas_height)

        self.graph_selection = None
        self.random_n = None

    # ------------------------------------------------------------------
    # UI Creation
    # ------------------------------------------------------------------
    def create_widgets(self):
        control_frame = ttk.Frame(self.root, padding=5)
        control_frame.pack(side=tk.TOP, fill=tk.X)

        self.graph_var = tk.StringVar(value="")
        ttk.Label(control_frame, text="Graph:").grid(row=0, column=0, padx=5)
        ttk.Radiobutton(control_frame, text="Existing Graph", variable=self.graph_var,
                        value="existing", command=self.on_graph_selection).grid(row=0, column=1, padx=5)
        ttk.Radiobutton(control_frame, text="Random Graph", variable=self.graph_var,
                        value="random", command=self.on_graph_selection).grid(row=0, column=2, padx=5)

        self.n_label = ttk.Label(control_frame, text="N (nodes):")
        self.n_entry = ttk.Entry(control_frame, width=5)
        self.generate_btn = ttk.Button(control_frame, text="Generate Random Graph",
                                       command=self.generate_random_graph, state=tk.DISABLED)

        ttk.Label(control_frame, text="Algorithm:").grid(row=0, column=3, padx=20)
        self.alg_var = tk.StringVar(value="BFS")
        alg_combo = ttk.Combobox(control_frame, textvariable=self.alg_var,
                                 values=["BFS", "DFS", "IDDFS", "Greedy Best-First", "A*"], width=15)
        alg_combo.grid(row=0, column=4, padx=5)

        ttk.Label(control_frame, text="Repeat:").grid(row=0, column=5, padx=5)
        self.repeat_count = tk.IntVar(value=1)
        repeat_spin = ttk.Spinbox(control_frame, from_=1, to=5, width=3,
                                  textvariable=self.repeat_count, state='readonly')
        repeat_spin.grid(row=0, column=6, padx=5)
        self.repeat_btn = ttk.Button(control_frame, text="Repeat Search (Avg)",
                                     command=self.run_repeated_search, state=tk.DISABLED)
        self.repeat_btn.grid(row=0, column=7, padx=5)

        self.start_btn = ttk.Button(control_frame, text="Start Search",
                                    command=self.start_animation, state=tk.DISABLED)
        self.start_btn.grid(row=0, column=8, padx=10)
        self.new_btn = ttk.Button(control_frame, text="New Search", command=self.new_search)
        self.new_btn.grid(row=0, column=9, padx=5)
        self.scatter_btn = ttk.Button(control_frame, text="Scatter Nodes",
                                      command=self.scatter_nodes, state=tk.DISABLED)
        self.scatter_btn.grid(row=0, column=10, padx=5)

        playback_frame = ttk.Frame(self.root, padding=5)
        playback_frame.pack(side=tk.TOP, fill=tk.X)

        self.play_pause_btn = ttk.Button(playback_frame, text="Pause",
                                         command=self.toggle_pause, state=tk.DISABLED)
        self.play_pause_btn.pack(side=tk.LEFT, padx=5)
        self.restart_anim_btn = ttk.Button(playback_frame, text="Restart",
                                           command=self.restart_animation, state=tk.DISABLED)
        self.restart_anim_btn.pack(side=tk.LEFT, padx=5)

        ttk.Label(playback_frame, text="Speed (steps/sec):").pack(side=tk.LEFT, padx=(20, 5))
        self.speed_var = tk.DoubleVar(value=2.0)
        speed_scale = ttk.Scale(playback_frame, from_=0.5, to=5.0, variable=self.speed_var,
                                orient=tk.HORIZONTAL, length=150, command=self.on_speed_change)
        speed_scale.pack(side=tk.LEFT, padx=5)
        self.speed_label = ttk.Label(playback_frame, text="2.0")
        self.speed_label.pack(side=tk.LEFT, padx=5)

        main_frame = ttk.Frame(self.root)
        main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(main_frame, bg="white", width=self.canvas_width, height=self.canvas_height)
        self.canvas.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.BOTH, expand=True)

        metrics_frame = ttk.Frame(main_frame)
        metrics_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.metrics_text = tk.Text(metrics_frame, wrap=tk.WORD, height=20, width=40)
        self.metrics_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.canvas.bind("<Motion>", self.on_node_motion)
        self.canvas.bind("<Button-1>", self.on_node_click)
        self.canvas.bind("<Leave>", self.clear_hover)

    # ------------------------------------------------------------------
    # Graph Loading and Drawing (unchanged from your working version)
    # ------------------------------------------------------------------
    def on_graph_selection(self):
        choice = self.graph_var.get()
        if choice == "existing":
            self.n_label.grid_forget()
            self.n_entry.grid_forget()
            self.generate_btn.grid_forget()
            self.load_existing_graph()
        elif choice == "random":
            self.n_label.grid(row=1, column=0, padx=5, pady=5)
            self.n_entry.grid(row=1, column=1, padx=5, pady=5)
            self.generate_btn.grid(row=1, column=2, padx=5, pady=5)
            self.generate_btn.config(state=tk.NORMAL)

    def load_existing_graph(self):
        self.graph = AdjacencyGraph()
        self.graph.load_coordinates("coordinates.csv")
        with open("Adjacencies.txt", 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                if len(parts) == 2:
                    node1, node2 = parts[0], parts[1]
                    if node1 in self.graph.nodes and node2 in self.graph.nodes:
                        self.graph.add_edge(node1, node2)
        lats = [node.latitude for node in self.graph.nodes.values()]
        lons = [node.longitude for node in self.graph.nodes.values()]
        if not lats:
            return
        min_lat, max_lat = min(lats), max(lats)
        min_lon, max_lon = min(lons), max(lons)
        margin = 100
        self.node_positions = {}
        for name, node in self.graph.nodes.items():
            x = margin + (node.longitude - min_lon) / (max_lon - min_lon) * (self.canvas_width - 2 * margin)
            y = margin + (node.latitude - min_lat) / (max_lat - min_lat) * (self.canvas_height - 2 * margin)
            self.node_positions[name] = (x, y)
        self.draw_graph()
        self.enable_start_selection()
        self.scatter_btn.config(state=tk.NORMAL)

    def generate_random_graph(self):
        try:
            n = int(self.n_entry.get())
            if n < 2:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "N must be an integer >= 2")
            return
        self.random_n = n
        self.graph = AdjacencyGraph()
        cols = math.ceil(math.sqrt(n))
        rows = math.ceil(n / cols)
        cell_w = (self.canvas_width - 200) / cols
        cell_h = (self.canvas_height - 200) / rows
        margin_x = 100
        margin_y = 100
        positions = {}
        for i in range(n):
            name = str(i + 1)
            min_lat, max_lat = 37.0, 40.0
            min_lon, max_lon = -102.0, -95.0
            lat = random.uniform(min_lat, max_lat)
            lon = random.uniform(min_lon, max_lon)
            self.graph.add_node(name, lat, lon)
            row = i // cols
            col = i % cols
            x = margin_x + col * cell_w + cell_w / 2
            y = margin_y + row * cell_h + cell_h / 2
            positions[name] = (x, y)
        self.node_positions = positions

        nodes = list(positions.keys())
        random.shuffle(nodes)
        for i in range(1, n):
            j = random.randint(0, i - 1)
            self.graph.add_edge(nodes[i], nodes[j])
        extra_edges = int(n * 0.2)
        attempts = 0
        while extra_edges > 0 and attempts < 1000:
            u = random.choice(nodes)
            v = random.choice(nodes)
            if u != v and v not in self.graph.get_neighbors(u):
                self.graph.add_edge(u, v)
                extra_edges -= 1
            attempts += 1
        self.draw_graph()
        self.enable_start_selection()
        self.scatter_btn.config(state=tk.NORMAL)

    def scatter_nodes(self):
        if not self.node_positions:
            return
        margin = self.node_radius + 20
        new_pos = {}
        for name, (x, y) in self.node_positions.items():
            dx = random.uniform(-20, 20)
            dy = random.uniform(-20, 20)
            nx = max(margin, min(self.canvas_width - margin, x + dx))
            ny = max(margin, min(self.canvas_height - margin, y + dy))
            new_pos[name] = (nx, ny)
        self.node_positions = new_pos
        self.draw_graph()

    def draw_graph(self):
        self.canvas.delete("all")
        self.node_circles.clear()
        self.node_texts.clear()
        self.edge_lines.clear()
        r = self.node_radius
        for name, node in self.graph.nodes.items():
            if name not in self.node_positions:
                continue
            x1, y1 = self.node_positions[name]
            for neighbor in node.adjacencies:
                if neighbor not in self.node_positions:
                    continue
                x2, y2 = self.node_positions[neighbor]
                line_id = self.canvas.create_line(x1, y1, x2, y2, fill="black", width=2)
                self.edge_lines.append((line_id, name, neighbor))
        for name, (x, y) in self.node_positions.items():
            fill = "white"
            if name == self.start_node:
                fill = "black"
            elif name == self.goal_node:
                fill = "black"
            elif name == self.current_node:
                fill = "dark green"
            elif name in self.frontier_set:
                fill = "blue"
            elif name in self.expanded_set:
                if self.final_parent and name not in self.get_final_path():
                    fill = "red"
                else:
                    fill = "yellow"
            circle = self.canvas.create_oval(x - r, y - r, x + r, y + r, fill=fill, outline="black", width=2)
            self.node_circles[name] = circle
            if name == self.start_node:
                text = self.canvas.create_text(x, y, text="Start", fill="green",
                                               font=("Arial", self.font_size + 2, "bold"))
            elif name == self.goal_node:
                text = self.canvas.create_text(x, y, text="Goal", fill="red",
                                               font=("Arial", self.font_size + 2, "bold"))
            else:
                text = self.canvas.create_text(x, y, text=name, fill="black",
                                               font=("Arial", self.font_size, "bold"))
            self.node_texts[name] = text
            if self.final_parent and name in self.expanded_set and name not in self.get_final_path():
                self.canvas.create_line(x - 8, y - 8, x + 8, y + 8, fill="black", width=2)
                self.canvas.create_line(x - 8, y + 8, x + 8, y - 8, fill="black", width=2)
        if self.final_parent and self.goal_node in self.final_parent:
            path_nodes = self.get_final_path()
            for line_id, u, v in self.edge_lines:
                if u in path_nodes and v in path_nodes and (
                        self.final_parent.get(v) == u or self.final_parent.get(u) == v):
                    self.canvas.itemconfig(line_id, fill="light green", width=4)
                else:
                    self.canvas.itemconfig(line_id, fill="black", width=2)

    def get_final_path(self):
        if not self.final_parent or self.goal_node not in self.final_parent:
            return []
        path = []
        cur = self.goal_node
        while cur is not None:
            path.append(cur)
            cur = self.final_parent.get(cur)
        path.reverse()
        return path if path and path[0] == self.start_node else []

    # ------------------------------------------------------------------
    # Start/Goal Selection
    # ------------------------------------------------------------------
    def enable_start_selection(self):
        self.phase = "start"
        self.start_node = None
        self.goal_node = None
        self.start_btn.config(state=tk.DISABLED)
        self.repeat_btn.config(state=tk.DISABLED)
        self.canvas.bind("<Motion>", self.on_node_motion)
        self.canvas.bind("<Button-1>", self.on_node_click)

    def clear_hover(self, event=None):
        if hasattr(self, 'hover_circle'):
            self.canvas.delete(self.hover_circle)
            delattr(self, 'hover_circle')
        if hasattr(self, 'hover_text'):
            self.canvas.delete(self.hover_text)
            delattr(self, 'hover_text')

    def on_node_motion(self, event):
        if self.phase not in ("start", "goal"):
            self.clear_hover()
            return
        r = self.node_radius
        for name, (x, y) in self.node_positions.items():
            if (event.x - x) ** 2 + (event.y - y) ** 2 <= r ** 2:
                self.clear_hover()
                text = "Start" if self.phase == "start" else "Goal"
                color = "green" if self.phase == "start" else "red"
                self.hover_circle = self.canvas.create_oval(x - r, y - r, x + r, y + r, fill="black", outline="black",
                                                            width=2)
                self.hover_text = self.canvas.create_text(x, y, text=text, fill=color,
                                                          font=("Arial", self.font_size + 2, "bold"))
                return
        self.clear_hover()

    def on_node_click(self, event):
        if self.phase not in ("start", "goal"):
            return
        r = self.node_radius
        for name, (x, y) in self.node_positions.items():
            if (event.x - x) ** 2 + (event.y - y) ** 2 <= r ** 2:
                if self.phase == "start" and name != self.goal_node:
                    self.start_node = name
                    self.phase = "goal"
                    self.draw_graph()
                    return
                elif self.phase == "goal" and name != self.start_node:
                    self.goal_node = name
                    self.phase = "done"
                    self.start_btn.config(state=tk.NORMAL)
                    self.repeat_btn.config(state=tk.NORMAL)
                    self.draw_graph()
                    return
        self.clear_hover()

    # ------------------------------------------------------------------
    # Animation (fixed)
    # ------------------------------------------------------------------
    def _run_silent_search(self, graph, algo, start, goal):
        """Run search non‑animated and return metrics (for accurate runtime)."""
        try:
            if algo == "BFS":
                gen = bfs(graph, start, goal, animate=False)
            elif algo == "DFS":
                gen = dfs(graph, start, goal, animate=False)
            elif algo == "IDDFS":
                gen = id_dfs(graph, start, goal, animate=False)
            elif algo == "Greedy Best-First":
                gen = greedy_best_first(graph, start, goal, animate=False)
            elif algo == "A*":
                gen = a_star(graph, start, goal, animate=False)
            else:
                return None

            while True:
                next(gen)
        except StopIteration as e:
            parent, metrics = e.value
            return metrics
        except Exception as e:
            print(f"Silent Search Failed: {e}")
            return None

    def start_animation(self):
        if not self.graph or not self.start_node or not self.goal_node:
            messagebox.showerror("Error", "Please select start and goal nodes.")
            return
        self.current_grid_config = (self.graph, self.alg_var.get())
        self._create_animation_generator()

    def _create_animation_generator(self):
        if not self.current_grid_config:
            return
        graph, algo = self.current_grid_config

        # Run silent search to get accurate metrics (true runtime)
        silent_metrics = self._run_silent_search(graph, algo, self.start_node, self.goal_node)
        if silent_metrics is None:
            # Fallback: metrics will come from generator (but runtime may be wrong)
            silent_metrics = None

        # Create animated generator
        try:
            if algo == "BFS":
                gen = bfs(graph, self.start_node, self.goal_node, animate=True)
            elif algo == "DFS":
                gen = dfs(graph, self.start_node, self.goal_node, animate=True)
            elif algo == "IDDFS":
                gen = id_dfs(graph, self.start_node, self.goal_node, animate=True)
            elif algo == "Greedy Best-First":
                gen = greedy_best_first(graph, self.start_node, self.goal_node, animate=True)
            elif algo == "A*":
                gen = a_star(graph, self.start_node, self.goal_node, animate=True)
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
        self.final_metrics = silent_metrics  # will be used at end
        self.play_pause_btn.config(state=tk.NORMAL, text="Pause")
        self.restart_anim_btn.config(state=tk.NORMAL)
        self.start_btn.config(state=tk.DISABLED)

        if self.anim_after_id:
            self.root.after_cancel(self.anim_after_id)
            self.anim_after_id = None

        self._animation_step()

    def _animation_step(self):
        if self.anim_paused:
            return
        try:
            current, frontier, expanded, parent = next(self.anim_gen)
            self.current_node = current
            self.frontier_set = frontier
            self.expanded_set = expanded
            self.anim_parent = parent
            self.draw_graph()
            delay_ms = int(1000 / self.anim_speed)
            self.anim_after_id = self.root.after(delay_ms, self._animation_step)
        except StopIteration as e:
            # Generator finished – extract final parent
            final_parent, gen_metrics = e.value
            self.final_parent = final_parent
            # Use silent metrics if available (accurate runtime), otherwise fallback to generator's
            if self.final_metrics is None:
                self.final_metrics = gen_metrics
            self.current_node = None
            self.frontier_set.clear()
            self.expanded_set.clear()
            self.draw_graph()
            self.display_metrics(self.final_metrics)
            self.play_pause_btn.config(state=tk.DISABLED)
            self.restart_anim_btn.config(state=tk.DISABLED)
            self.start_btn.config(state=tk.NORMAL)
            self.anim_gen = None
            self.anim_after_id = None

    def toggle_pause(self):
        if self.anim_gen is None:
            return
        self.anim_paused = not self.anim_paused
        self.play_pause_btn.config(text="Play" if self.anim_paused else "Pause")
        if self.anim_paused:
            if self.anim_after_id:
                self.root.after_cancel(self.anim_after_id)
                self.anim_after_id = None
        else:
            if self.anim_after_id is None and self.anim_gen is not None:
                self._animation_step()

    def restart_animation(self):
        if self.anim_gen is None and not self.current_grid_config:
            return
        if self.anim_after_id:
            self.root.after_cancel(self.anim_after_id)
            self.anim_after_id = None
        self._create_animation_generator()

    def on_speed_change(self, event=None):
        self.anim_speed = self.speed_var.get()
        self.speed_label.config(text=f"{self.anim_speed:.1f}")

    # ------------------------------------------------------------------
    # Metrics Display
    # ------------------------------------------------------------------
    def display_metrics(self, metrics):
        self.metrics_text.delete(1.0, tk.END)
        if not metrics:
            self.metrics_text.insert(tk.END, "No metrics available.")
            return
        for key, value in metrics.items():
            if isinstance(value, float):
                formatted_value = f"{value:.8f}"
            else:
                formatted_value = str(value)
            if key == 'runtime':
                formatted_value += " S"
                display_key = key
            elif key == 'Path Cost':
                display_key = "Path Cost (km)"
            elif key == '(averaged over)':
                display_key = "Averaged over"
            else:
                display_key = key
            self.metrics_text.insert(tk.END, f"{display_key}: {formatted_value}\n")

    # ------------------------------------------------------------------
    # Repeat Search (non‑animated, already accurate)
    # ------------------------------------------------------------------
    def run_repeated_search(self):
        if not self.graph or not self.start_node or not self.goal_node:
            messagebox.showerror("Error", "Please select start and goal nodes first.")
            return
        try:
            n = int(self.repeat_count.get())
            if n < 1 or n > 5:
                raise ValueError
        except:
            messagebox.showerror("Error", "Repeat count must be between 1 and 5.")
            return

        algo = self.alg_var.get()
        metrics_list = []
        for _ in range(n):
            try:
                if algo == "BFS":
                    gen = bfs(self.graph, self.start_node, self.goal_node, animate=False)
                elif algo == "DFS":
                    gen = dfs(self.graph, self.start_node, self.goal_node, animate=False)
                elif algo == "IDDFS":
                    gen = id_dfs(self.graph, self.start_node, self.goal_node, animate=False)
                elif algo == "Greedy Best-First":
                    gen = greedy_best_first(self.graph, self.start_node, self.goal_node, animate=False)
                elif algo == "A*":
                    gen = a_star(self.graph, self.start_node, self.goal_node, animate=False)
                else:
                    return

                while True:
                    next(gen)
            except StopIteration as e:
                parent, metrics = e.value
                metrics_list.append(metrics)
            except Exception as e:
                messagebox.showerror("Error", f"Search failed: {e}")
                return
        avg_metrics = {}
        for key in metrics_list[0].keys():
            values = [m[key] for m in metrics_list]
            if all(isinstance(v, (int, float)) for v in values):
                avg_metrics[key] = sum(values) / n
            else:
                avg_metrics[key] = values[0]
        avg_metrics['(Averaged Over)'] = f"{n} runs"
        self.display_metrics(avg_metrics)

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------
    def new_search(self):
        if self.anim_after_id:
            self.root.after_cancel(self.anim_after_id)
            self.anim_after_id = None
        self.start_node = None
        self.goal_node = None
        self.phase = "start"
        self.current_node = None
        self.frontier_set.clear()
        self.expanded_set.clear()
        self.anim_parent.clear()
        self.final_parent = None
        self.final_metrics = None
        self.anim_gen = None
        self.anim_paused = False
        self.current_grid_config = None
        self.start_btn.config(state=tk.DISABLED)
        self.repeat_btn.config(state=tk.DISABLED)
        self.play_pause_btn.config(state=tk.DISABLED)
        self.restart_anim_btn.config(state=tk.DISABLED)
        self.scatter_btn.config(state=tk.DISABLED)
        self.metrics_text.delete(1.0, tk.END)
        self.graph = None
        self.node_positions.clear()
        self.canvas.delete("all")
        self.graph_var.set("")
        self.n_label.grid_forget()
        self.n_entry.grid_forget()
        self.generate_btn.grid_forget()


if __name__ == "__main__":
    root = tk.Tk()
    app = AdjacencyGraphSearchGUI(root)
    root.mainloop()
