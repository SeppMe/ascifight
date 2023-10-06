from abc import ABC, abstractmethod

from ascifight.board.data import Coordinates
from ascifight.client_lib.object import Objects

from ascifight.board.actions import Directions


class Metric(ABC):
    def __init__(self, objects: Objects):
        self.objects = objects
        self.distance_fields: dict[Coordinates, dict[Coordinates, float]] = {}
        self.paths: dict[tuple[Coordinates, Coordinates], list[Coordinates]] = {}

    def distance(self, origin: Coordinates, destination: Coordinates) -> int:
        """
        The distance between origin and destination in steps.
        """
        return len(self.path(origin, destination)) - 1

    def distance_field(self, origin: Coordinates) -> dict[Coordinates, float]:
        """
        The weighted distance to each map coordinates from an origin coordinate.
        If no weights are given the distances are equal to the path length.
        If weights are given, the distance depends on the weights used
        """
        if origin in self.distance_fields:
            result = self.distance_fields[origin]
        else:
            result = self._distance_field(origin)
            self.distance_fields[origin] = result
        return result

    def path(self, origin: Coordinates, destination: Coordinates) -> list[Coordinates]:
        """
        The shortest path from an origin coordinate to a destination coordinate.
        """
        if (origin, destination) in self.paths:
            result = self.paths[(origin, destination)]
        else:
            result = self._path(origin, destination)
            self.paths[(origin, destination)] = result
        return result

    def next_direction(
        self,
        origin: Coordinates,
        destination: Coordinates,
    ) -> Directions:
        """
        The next direction to move on the shortest path from the origin coordinate to
        the destination coordinate.
        """
        next = self.path(origin, destination)[1]

        if origin.x == next.x:
            if next.y > origin.y:
                direction = Directions.up
            else:
                direction = Directions.down
        else:
            if next.x > origin.x:
                direction = Directions.right
            else:
                direction = Directions.left
        return direction

    @abstractmethod
    def _distance_field(self, origin: Coordinates) -> dict[Coordinates, float]:
        pass

    def _path(self, origin: Coordinates, destination: Coordinates) -> list[Coordinates]:
        path: list[Coordinates] = [destination]
        distance_field = self.distance_field(origin)
        next = destination
        while next != origin:
            neighbors = self._neighbors(path[-1])
            distances = [
                (distance_field[coordinates], coordinates) for coordinates in neighbors
            ]
            next = sorted(distances, key=lambda x: x[0])[0][1]
            path.append(next)
        path.reverse()
        return path

    def _in_bounds(self, coordinates) -> bool:
        x, y = coordinates
        map_size = self.objects.rules.map_size
        return 0 <= x < map_size and 0 <= y < map_size

    def _neighbors(self, coordinates: Coordinates) -> list[Coordinates]:
        (x, y) = coordinates.x, coordinates.y
        coords = filter(
            self._in_bounds, [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
        )
        return [Coordinates(x=x, y=y) for x, y in coords]


class BasicMetric(Metric):
    def _distance_field(self, origin: Coordinates) -> dict[Coordinates, float]:
        distance_field: dict[Coordinates, float] = {}
        for i in range(self.objects.rules.map_size):
            for j in range(self.objects.rules.map_size):
                coordinates = Coordinates(x=i, y=j)
                distance = self._distance(origin, coordinates)
                distance_field[coordinates] = distance
        return distance_field

    def _distance(
        self,
        origin: Coordinates,
        destination: Coordinates,
    ) -> int:
        """
        Calculate the distance in steps between origin and destination coordinates.
        """
        x, y = self._distance_vector(origin, destination)
        return abs(x) + abs(y)

    def _distance_vector(
        self,
        origin: Coordinates,
        destination: Coordinates,
    ) -> tuple[int, int]:
        """
        Calculate the distance vector between origin and destination coordinates.
        """
        x = destination.x - origin.x
        y = destination.y - origin.y
        return x, y
