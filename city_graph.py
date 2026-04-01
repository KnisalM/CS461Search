from typing import List, Any


class Node:
    def __init__(self, name, lat, long):
        self.name = name
        self.latitude = lat
        self.longitude = long
        self.adjacencies = []


class CityGraph:
    nodes: List[Node]

    def __init__(self, start, goal):
        self.nodes = []
        self.start_city = start
        self.goal_city = goal

    def valid_city(self, city):
        return city in self.nodes

    def get_max_depth(self):
        return len(self.nodes)
            
