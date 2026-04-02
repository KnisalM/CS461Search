import tkinter as tk
from tkinter import ttk, messagebox
import random
import math
from collections import deque
from adjacency_graph import AdjacencyGraph
from search import bfs, dfs, id_dfs, greedy_best_first, a_star

class BatchGraphSearchGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Batch Graph Search – Compare Searches")

        # Graph and state
        self.graph = None
        self.node_positions = {}
        self.node_circles = {}
        self.node_texts = {}
        self.edge_lines = []
        self.start_node = None
        self.goal_node = None
        self.phase = "start"   # "start", "goal", "done"

        # Queue storage and graph numbering
        self.search_queue = []       # list of dicts
        self.graph_counter = 0       # total number of distinct configurations created
        self.current_config_id = None # ID of the currently displayed configuration (graph+start+goal)

        # Canvas size
        self.canvas_width = 1200
        self.canvas_height = 900
        self.node_radius = 18
        self.font_size = 8

        self.create_widgets()
        self.canvas.config(width=self.canvas_width, height=self.canvas_height)

    # ------------------------------------------------------------------
    # UI Creation
    # ------------------------------------------------------------------
    def create_widgets(self):
        # Top control frame
        control_frame = ttk.Frame(self.root, padding=5)
        control_frame.pack(side=tk.TOP, fill=tk.X)

        # Graph selection
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

        # Algorithm selection
        ttk.Label(control_frame, text="Algorithm:").grid(row=0, column=3, padx=20)
        self.alg_var = tk.StringVar(value="BFS")
        alg_combo = ttk.Combobox(control_frame, textvariable=self.alg_var,
                                 values=["BFS", "DFS", "IDDFS", "Greedy Best-First", "A*"], width=15)
        alg_combo.grid(row=0, column=4, padx=5)

        # Buttons
        self.add_btn = ttk.Button(control_frame, text="Add Search",
                                  command=self.add_search, state=tk.DISABLED)
        self.add_btn.grid(row=0, column=5, padx=10)

        self.reset_start_goal_btn = ttk.Button(control_frame, text="Reset Start/Goal",
                                               command=self.reset_start_goal, state=tk.NORMAL)
        self.reset_start_goal_btn.grid(row=0, column=6, padx=5)

        self.begin_btn = ttk.Button(control_frame, text="Begin Batch",
                                    command=self.begin_batch, state=tk.DISABLED)
        self.begin_btn.grid(row=0, column=7, padx=10)

        self.new_btn = ttk.Button(control_frame, text="New Search (Reset All)",
                                  command=self.new_search)
        self.new_btn.grid(row=0, column=8, padx=5)

        # Main display area
        main_frame = ttk.Frame(self.root)
        main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Left: canvas
        self.canvas = tk.Canvas(main_frame, bg="white", width=self.canvas_width, height=self.canvas_height)
        self.canvas.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Right: queue panel and results
        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Queue list frame
        queue_frame = ttk.LabelFrame(right_panel, text="Search Queue", padding=5)
        queue_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.queue_canvas = tk.Canvas(queue_frame, bg="white", height=200)
        v_scroll = ttk.Scrollbar(queue_frame, orient=tk.VERTICAL, command=self.queue_canvas.yview)
        self.queue_canvas.configure(yscrollcommand=v_scroll.set)
        self.queue_inner = ttk.Frame(self.queue_canvas)
        self.queue_canvas.create_window((0,0), window=self.queue_inner, anchor="nw")
        self.queue_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.queue_inner.bind("<Configure>", lambda e: self.queue_canvas.configure(scrollregion=self.queue_canvas.bbox("all")))

        # Results table with scrollbars
        results_frame = ttk.LabelFrame(right_panel, text="Batch Results", padding=5)
        results_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        tree_container = ttk.Frame(results_frame)
        tree_container.pack(fill=tk.BOTH, expand=True)

        v_scroll_tree = ttk.Scrollbar(tree_container, orient=tk.VERTICAL)
        h_scroll_tree = ttk.Scrollbar(tree_container, orient=tk.HORIZONTAL)

        self.tree = ttk.Treeview(tree_container,
                                 columns=("Algo", "Graph", "Start", "Goal", "Runtime", "Generated", "Expanded",
                                          "Peak Frontier", "Avg Branch", "Max Branch", "Depth", "Path Cost"),
                                 show="headings",
                                 yscrollcommand=v_scroll_tree.set,
                                 xscrollcommand=h_scroll_tree.set)
        v_scroll_tree.config(command=self.tree.yview)
        h_scroll_tree.config(command=self.tree.xview)

        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=90)

        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scroll_tree.grid(row=0, column=1, sticky="ns")
        h_scroll_tree.grid(row=1, column=0, sticky="ew")
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)

        # Bind mouse events for node selection
        self.canvas.bind("<Motion>", self.on_node_motion)
        self.canvas.bind("<Button-1>", self.on_node_click)
        self.canvas.bind("<Leave>", self.clear_hover)

    # ------------------------------------------------------------------
    # Graph Loading and Drawing
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
        self._map_positions()
        self._reset_start_goal_state()  # clear start/goal, phase to start, no config ID yet
        self.draw_graph()
        self.enable_start_selection()

    def generate_random_graph(self):
        try:
            n = int(self.n_entry.get())
            if n < 2:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "N must be an integer >= 2")
            return
        self.graph = AdjacencyGraph()
        cols = math.ceil(math.sqrt(n))
        rows = math.ceil(n / cols)
        cell_w = (self.canvas_width - 200) / cols
        cell_h = (self.canvas_height - 200) / rows
        margin_x, margin_y = 100, 100
        positions = {}
        for i in range(n):
            name = str(i+1)
            min_lat, max_lat = 37.0, 40.0
            min_lon, max_lon = -102.0, -95.0
            lat = random.uniform(min_lat, max_lat)
            lon = random.uniform(min_lon, max_lon)
            self.graph.add_node(name, lat, lon)
            row = i // cols
            col = i % cols
            x = margin_x + col * cell_w + cell_w/2
            y = margin_y + row * cell_h + cell_h/2
            positions[name] = (x, y)
        self.node_positions = positions

        # Build spanning tree
        nodes = list(positions.keys())
        random.shuffle(nodes)
        for i in range(1, n):
            j = random.randint(0, i-1)
            self.graph.add_edge(nodes[i], nodes[j])
        # Add extra edges
        extra = int(n * 0.2)
        attempts = 0
        while extra > 0 and attempts < 1000:
            u = random.choice(nodes)
            v = random.choice(nodes)
            if u != v and v not in self.graph.get_neighbors(u):
                self.graph.add_edge(u, v)
                extra -= 1
            attempts += 1
        self._reset_start_goal_state()
        self.draw_graph()
        self.enable_start_selection()

    def _map_positions(self):
        lats = [node.latitude for node in self.graph.nodes.values()]
        lons = [node.longitude for node in self.graph.nodes.values()]
        if not lats:
            return
        min_lat, max_lat = min(lats), max(lats)
        min_lon, max_lon = min(lons), max(lons)
        margin = 100
        self.node_positions = {}
        for name, node in self.graph.nodes.items():
            x = margin + (node.longitude - min_lon) / (max_lon - min_lon) * (self.canvas_width - 2*margin)
            y = margin + (node.latitude - min_lat) / (max_lat - min_lat) * (self.canvas_height - 2*margin)
            self.node_positions[name] = (x, y)

    def draw_graph(self):
        self.canvas.delete("all")
        self.node_circles.clear()
        self.node_texts.clear()
        self.edge_lines.clear()
        r = self.node_radius
        # Edges
        for name, node in self.graph.nodes.items():
            if name not in self.node_positions: continue
            x1, y1 = self.node_positions[name]
            for nb in node.adjacencies:
                if nb not in self.node_positions: continue
                x2, y2 = self.node_positions[nb]
                line_id = self.canvas.create_line(x1, y1, x2, y2, fill="black", width=2)
                self.edge_lines.append((line_id, name, nb))
        # Nodes
        for name, (x, y) in self.node_positions.items():
            fill = "white"
            if name == self.start_node or name == self.goal_node:
                fill = "black"
            circle = self.canvas.create_oval(x-r, y-r, x+r, y+r, fill=fill, outline="black", width=2)
            self.node_circles[name] = circle
            if name == self.start_node:
                self.canvas.create_text(x, y, text="Start", fill="green", font=("Arial", self.font_size+2, "bold"))
            elif name == self.goal_node:
                self.canvas.create_text(x, y, text="Goal", fill="red", font=("Arial", self.font_size+2, "bold"))
            else:
                self.canvas.create_text(x, y, text=name, fill="black", font=("Arial", self.font_size, "bold"))

    # ------------------------------------------------------------------
    # Start/Goal Selection and Reset
    # ------------------------------------------------------------------
    def _reset_start_goal_state(self):
        """Clear start/goal, reset phase, and invalidate current configuration ID."""
        self.start_node = None
        self.goal_node = None
        self.phase = "start"
        self.current_config_id = None
        self.add_btn.config(state=tk.DISABLED)
        self.draw_graph()

    def reset_start_goal(self):
        """Button callback: reset start and goal without affecting the graph."""
        self._reset_start_goal_state()
        self.enable_start_selection()

    def enable_start_selection(self):
        self.phase = "start"
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
            if (event.x - x)**2 + (event.y - y)**2 <= r**2:
                self.clear_hover()
                text = "Start" if self.phase == "start" else "Goal"
                color = "green" if self.phase == "start" else "red"
                self.hover_circle = self.canvas.create_oval(x-r, y-r, x+r, y+r, fill="black", outline="black", width=2)
                self.hover_text = self.canvas.create_text(x, y, text=text, fill=color, font=("Arial", self.font_size+2, "bold"))
                return
        self.clear_hover()

    def on_node_click(self, event):
        if self.phase not in ("start", "goal"):
            return
        r = self.node_radius
        for name, (x, y) in self.node_positions.items():
            if (event.x - x)**2 + (event.y - y)**2 <= r**2:
                if self.phase == "start" and name != self.goal_node:
                    self.start_node = name
                    self.phase = "goal"
                    self.draw_graph()
                    return
                elif self.phase == "goal" and name != self.start_node:
                    self.goal_node = name
                    self.phase = "done"
                    # New configuration complete – assign a new ID
                    self.graph_counter += 1
                    self.current_config_id = self.graph_counter
                    self.add_btn.config(state=tk.NORMAL)
                    self.draw_graph()
                    return
        self.clear_hover()

    # ------------------------------------------------------------------
    # Batch Queue Management
    # ------------------------------------------------------------------
    def add_search(self):
        if not self.graph or not self.start_node or not self.goal_node:
            messagebox.showerror("Error", "Please select a graph, start and goal nodes.")
            return
        if len(self.search_queue) >= 25:
            messagebox.showerror("Error", "Queue limit (25) reached. Remove some items or run batch.")
            return

        # Deep copy the current graph
        graph_copy = self.graph.deep_copy()
        config_id = self.current_config_id

        self.search_queue.append({
            'graph': graph_copy,
            'start': self.start_node,
            'goal': self.goal_node,
            'algorithm': self.alg_var.get(),
            'graph_id': config_id
        })

        # Refresh queue display
        self.refresh_queue_display()

        # Enable begin button if queue not empty
        self.begin_btn.config(state=tk.NORMAL if self.search_queue else tk.DISABLED)

    def remove_search(self, index):
        del self.search_queue[index]
        self.refresh_queue_display()
        self.begin_btn.config(state=tk.NORMAL if self.search_queue else tk.DISABLED)

    def refresh_queue_display(self):
        """Clear and rebuild the queue panel."""
        for widget in self.queue_inner.winfo_children():
            widget.destroy()
        for i, item in enumerate(self.search_queue, start=1):
            frame = ttk.Frame(self.queue_inner)
            frame.pack(fill=tk.X, pady=2)
            label = ttk.Label(frame, text=f"{i}. {item['algorithm']} on Graph #{item['graph_id']}  ({item['start']} → {item['goal']})")
            label.pack(side=tk.LEFT)
            remove_btn = ttk.Button(frame, text="Remove", command=lambda idx=i-1: self.remove_search(idx))
            remove_btn.pack(side=tk.RIGHT)

    # ------------------------------------------------------------------
    # Run Batch
    # ------------------------------------------------------------------
    def _run_silent_search(self, graph, algo, start, goal):
        """Return metrics dict for a single search (non-animated)."""
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
            return None

    def begin_batch(self):
        if not self.search_queue:
            messagebox.showerror("Error", "No searches in queue.")
            return

        # Clear previous results
        for row in self.tree.get_children():
            self.tree.delete(row)

        for idx, job in enumerate(self.search_queue, start=1):
            metrics = self._run_silent_search(job['graph'], job['algorithm'], job['start'], job['goal'])
            if metrics is None:
                self.tree.insert("", tk.END, values=(job['algorithm'], f"#{job['graph_id']}", job['start'], job['goal'],
                                                     "ERROR", "", "", "", "", "", "", ""))
                continue
            # Extract values
            runtime = f"{metrics['runtime']:.6f} s"
            gen = metrics['Nodes Generated']
            exp = metrics['Nodes Expanded']
            peak = metrics['Peak Frontier Size']
            avg_branch = f"{metrics['Average Branching Factor']:.2f}"
            max_branch = metrics['Max Branching Factor']
            depth = metrics['Solution Depth']
            cost = f"{metrics['Path Cost']:.2f} km"
            self.tree.insert("", tk.END, values=(job['algorithm'], f"#{job['graph_id']}", job['start'], job['goal'],
                                                 runtime, gen, exp, peak, avg_branch, max_branch, depth, cost))
            self.tree.update_idletasks()

        messagebox.showinfo("Batch Complete", f"Ran {len(self.search_queue)} searches.\nResults displayed in table.")

    # ------------------------------------------------------------------
    # Reset All
    # ------------------------------------------------------------------
    def new_search(self):
        """Reset everything: clear queue, reset graph, start/goal, and counter."""
        if self.anim_after_id:  # not used in batch, but safe
            self.root.after_cancel(self.anim_after_id)
        self.graph = None
        self.start_node = None
        self.goal_node = None
        self.phase = "start"
        self.node_positions.clear()
        self.canvas.delete("all")
        self.graph_var.set("")
        self.n_label.grid_forget()
        self.n_entry.grid_forget()
        self.generate_btn.grid_forget()
        self.add_btn.config(state=tk.DISABLED)
        self.begin_btn.config(state=tk.DISABLED)
        # Clear queue
        self.search_queue.clear()
        self.refresh_queue_display()
        # Clear tree
        for row in self.tree.get_children():
            self.tree.delete(row)
        # Reset counter and current ID
        self.graph_counter = 0
        self.current_config_id = None
        self.enable_start_selection()

if __name__ == "__main__":
    root = tk.Tk()
    app = BatchGraphSearchGUI(root)
    root.mainloop()
