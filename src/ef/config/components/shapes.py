import numpy as np
import rowan
from numpy.linalg import norm

from ef.config.component import ConfigComponent
from ef.util.serializable_h5 import SerializableH5

__all__ = ['Shape', 'Box', 'Cylinder', 'Tube', 'Sphere', 'Cone']


class Shape(ConfigComponent, SerializableH5):
    def visualize(self, visualizer, **kwargs):
        raise NotImplementedError()

    def are_positions_inside(self, positions):
        raise NotImplementedError()

    def generate_uniform_random_position(self, random_state):
        return self.generate_uniform_random_posititons(random_state, 1)[0]

    def generate_uniform_random_posititons(self, random_state, n):
        raise NotImplementedError()


def rotation_from_z(vector):
    """
    Find a quaternion that rotates z-axis into a given vector.
    :param vector: Any non-zero 3-component vector
    :return: Array of length 4 with the rotation quaternion
    """
    axis = np.cross((0, 0, 1), vector)
    if norm(axis) == 0:
        return np.array((1, 0, 0, 0))
    cos2 = (vector / norm(vector))[2]
    cos = np.sqrt((1 + cos2) / 2)
    sin = np.sqrt((1 - cos2) / 2)
    vector_component = axis / norm(axis) * sin
    return np.concatenate(([cos], vector_component))


class Box(Shape):
    def __init__(self, origin=(0, 0, 0), size=(1, 1, 1)):
        self.origin = np.array(origin, np.float)
        self.size = np.array(size, np.float)

    def visualize(self, visualizer, **kwargs):
        visualizer.draw_box(self.size, self.origin, **kwargs)

    def are_positions_inside(self, positions):
        return np.logical_and(np.all(positions >= self.origin, axis=-1),
                              np.all(positions <= self.origin + self.size, axis=-1))

    def generate_uniform_random_posititons(self, random_state, n):
        return random_state.uniform(self.origin, self.origin + self.size, (n, 3))


class Cylinder(Shape):
    def __init__(self, start=(0, 0, 0), end=(1, 0, 0), radius=1):
        self.start = np.array(start, np.float)
        self.end = np.array(end, np.float)
        self.radius = float(radius)
        self._rotation = rotation_from_z(self.end - self.start)

    def visualize(self, visualizer, **kwargs):
        visualizer.draw_cylinder(self.start, self.end, self.radius, **kwargs)

    def are_positions_inside(self, positions):
        pointvec = positions - self.start
        axisvec = self.end - self.start
        axis = norm(axisvec)
        unit_axisvec = axisvec / axis
        # for one-point case, dot would return a scalar, so it's cast to array explicitly
        projection = np.asarray(np.dot(pointvec, unit_axisvec))
        perp_to_axis = norm(pointvec - unit_axisvec[np.newaxis] * projection[..., np.newaxis], axis=-1)
        result = np.logical_and.reduce([0 <= projection, projection <= axis, perp_to_axis <= self.radius])
        return result

    def generate_uniform_random_posititons(self, random_state, n):
        r = np.sqrt(random_state.uniform(0.0, 1.0, n)) * self.radius
        phi = random_state.uniform(0.0, 2.0 * np.pi, n)
        x = r * np.cos(phi)
        y = r * np.sin(phi)
        z = random_state.uniform(0.0, norm(self.end - self.start), n)
        points = np.stack((x, y, z), -1)
        return rowan.rotate(self._rotation, points) + self.start


class Tube(Shape):
    def __init__(self, start=(0, 0, 0), end=(1, 0, 0), inner_radius=1, outer_radius=2):
        self.start = np.array(start, np.float)
        self.end = np.array(end, np.float)
        self.inner_radius = float(inner_radius)
        self.outer_radius = float(outer_radius)
        self._rotation = rotation_from_z(self.end - self.start)

    def visualize(self, visualizer, **kwargs):
        visualizer.draw_tube(self.start, self.end, self.inner_radius, self.outer_radius, **kwargs)

    def are_positions_inside(self, positions):
        pointvec = positions - self.start
        axisvec = self.end - self.start
        axis = norm(axisvec)
        unit_axisvec = axisvec / axis
        # for one-point case, dot would return a scalar, so it's cast to array explicitly
        projection = np.asarray(np.dot(pointvec, unit_axisvec))
        perp_to_axis = norm(pointvec - unit_axisvec[np.newaxis] * projection[..., np.newaxis], axis=-1)
        return np.logical_and.reduce(
            [0 <= projection, projection <= axis, self.inner_radius <= perp_to_axis, perp_to_axis <= self.outer_radius])

    def generate_uniform_random_posititons(self, random_state, n):
        r = np.sqrt(random_state.uniform(self.inner_radius / self.outer_radius, 1.0, n)) * self.outer_radius
        phi = random_state.uniform(0.0, 2.0 * np.pi, n)
        x = r * np.cos(phi)
        y = r * np.sin(phi)
        z = random_state.uniform(0.0, norm(self.end - self.start), n)
        points = np.stack((x, y, z), -1)
        return rowan.rotate(self._rotation, points) + self.start


class Sphere(Shape):
    def __init__(self, origin=(0, 0, 0), radius=1):
        self.origin = np.array(origin)
        self.radius = float(radius)

    def visualize(self, visualizer, **kwargs):
        visualizer.draw_sphere(self.origin, self.radius, **kwargs)

    def are_positions_inside(self, positions):
        return norm(positions - self.origin, axis=-1) <= self.radius

    def generate_uniform_random_posititons(self, random_state, n):
        while True:
            p = random_state.uniform(-1, 1, (n * 2, 3)) * self.radius + self.origin
            p = p.compress(self.are_positions_inside(p), 0)
            if len(p) > n:
                return p[:n]


class Cone(Shape):
    def __init__(self, start=(0, 0, 0, 1),
                 start_radii=(1, 2), end_radii=(3, 4)):
        self.start = np.array(start, np.float)
        self.start_radii = np.array(start_radii, np.float)
        self.end_radii = np.array(end_radii, np.float)

    def visualize(self, visualizer, **kwargs):
        visualizer.draw_cone(self.start, self.end,
                             self.start_radii, self.end_radii, **kwargs)

# TODO: def are_positions_inside(self, point)
