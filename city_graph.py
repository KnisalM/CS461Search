
class Node:
    def __init__(self, name, lat, long):
        self.name = name
        self.latitude = lat
        self.longitude = long
        self.adjacencies = []

class CityGraph:
    def __init__(self, name, lat, long):

