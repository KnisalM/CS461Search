from typing import List, Any
from math import sqrt


class Node:
    def __init__(self, name, lat, long):
        self.name = name
        self.latitude = lat
        self.longitude = long
        self.adjacencies = []


class CityGraph:

    def __init__(self):
        self.nodes = {}

    def in_bounds(self, city):
        return city in self.nodes

    def get_max_depth(self):
        return len(self.nodes)

    def add_node(self, name, lat, long):
        self.nodes[name] = Node(name, lat, long)

    def add_edge(self, city1, city2):
        # Project defines that each city has symmetric adjacency
        self.nodes[city1].adjacencies.append(city2)
        self.nodes[city2].adjacencies.append(city1)

    def get_neighbors(self, city):
        return self.nodes[city].adjacencies

    def is_traversable(self, city):
        # All cities are traversable, need function name for search algs to continue operating as expected
        return city in self.nodes

    def heuristic_method(self, city_1, city_2):
        """Defining the heuristic method for this class will require calculating the changes in their coordinate locations
        While coordinate locations are not the same as locations on a grid, and do not correlate directly to
        straight line distance, it is an admissible heuristic for the point of this project. This function will work
        by using the pythagorean theorem and calculating the theoretical straight line coordinate distance"""
        delta_lat = self.nodes[city_2].latitude - self.nodes[city_1].latitude
        delta_long = self.nodes[city_2].longitude - self.nodes[city_1].longitude
        return sqrt((delta_lat**2) + (delta_long**2))
