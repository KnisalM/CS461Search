import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys

class Launcher:
    def __init__(self, root):
        self.root = root
        self.root.title("Graph Search Visualizer Launcher - Select Your Mode")
        self.root.geometry("500x250")
        self.root.resizable(False, False)

        ttk.Label(root, text="Select Search Mode", font=("Arial", 16)).pack(pady=20)

        ttk.Button(root, text="2D Grid Search w/animation", width=25, command=self.launch_2d).pack(pady=10)
        ttk.Button(root, text="Single Search Adjacency Graph", width=25, command=self.launch_single).pack(pady=10)
        ttk.Button(root, text="Batch Mode (Compare Searches)", width=25, command=self.launch_batch).pack(pady=10)


