from typing import List, Any
from math import sqrt, sin, cos, atan2, radians


def haversine_conversion(lat1, lat2, lon1, lon2):
    """Adding the haversine conversion, currently my Path Cost for the adjacency graph is returning
    Change in degrees, not any actual useable distance, need this to be in a unit that is readable and understandable"""
    R = 6371.0  # This is earth's approximate radius in Kilometers
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

class Node:
    def __init__(self, name, lat, long):
        self.name = name
        self.latitude = lat
        self.longitude = long
        self.adjacencies = []


class AdjacencyGraph:

    def __init__(self):
        self.nodes = {}

    def in_bounds(self, node):
        return node in self.nodes

    def get_max_depth(self):
        return len(self.nodes)

    def add_node(self, name, lat, long):
        self.nodes[name] = Node(name, lat, long)

    def add_edge(self, node1, node2):
        # Project defines that each node has symmetric adjacency
        self.nodes[node1].adjacencies.append(node2)
        self.nodes[node2].adjacencies.append(node1)

    def get_neighbors(self, node):
        return self.nodes[node].adjacencies

    def is_traversable(self, node):
        # All nodes are traversable, need function name for search algs to continue operating as expected
        return node in self.nodes

    def heuristic_method(self, node_1, node_2):
        """Defining the heuristic method for this class will require calculating the changes in their coordinate locations
        While coordinate locations are not the same as locations on a grid, and do not correlate directly to
        straight line distance, it is an admissible heuristic for the point of this project. This function will work
        by using the pythagorean theorem and calculating the theoretical straight line coordinate distance"""
        n1 = self.nodes[node_1]
        n2 = self.nodes[node_2]
        return haversine_conversion(n1.latitude, n2.latitude, n1.longitude, n2.longitude)

    def load_coordinates(self, filename):
        # Reads the CSV file and adds nodes to the AdjacencyGraph object
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                name, lat, lon = line.split(',')
                lat = float(lat.strip())
                lon = float(lon.strip())
                self.add_node(name.strip(), lat, lon)

    def load_adjacencies(self, filename):
        # Reads the adjacency file and adds edges to Nodes
        with open(filename, 'r') as f:
            for line in f:
                adjacencies = line.strip().split()
                if len(adjacencies) == 2:
                    self.add_edge(adjacencies[0], adjacencies[1])

    def get_cost(self, n1, n2):
        return self.heuristic_method(n1, n2)

    def calculate_path_cost(self, parent, goal):
        """This function will work for both unweighted grids and adjacency graphs
        Calculating the cost of the total path. In the weighted grid, this will use the get_cost
        function which calculates node to node cost, and then it will sum each traversal and
        return total path cost"""
        if goal not in parent:
            return float('inf')

        total_cost = 0.0
        current = goal
        while parent[current] is not None:
            prev = parent[current]
            total_cost += self.get_cost(prev, current)
            current = prev
        return total_cost

    def deep_copy(self):
        # Return a deep copy of the adjacency graph item so that they can be stored for batch processing
        new_graph = AdjacencyGraph()
        # make copies of all Nodes
        for name, node in self.nodes.items():
            new_graph.add_node(name, node.latitude, node.longitude)
        # Copy all the edges
        for name, node in self.nodes.items():
            for neighbor in node.adjacencies:
                if name < neighbor:
                    new_graph.add_edge(name, neighbor)
        return new_graph
