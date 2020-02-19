from math import sqrt

import numpy as np
import pytest
from numpy.random import RandomState
from numpy.testing import assert_array_almost_equal

from ef.config.components import Cylinder, Tube
from ef.config.components.shapes import Box, Sphere, rotation_from_z


@pytest.mark.usefixtures("backend")
class TestShapes:
    def test_rotation_from_z(self):
        r2 = 1 / sqrt(2)
        assert_array_almost_equal(rotation_from_z(np.array([1, 0, 0])), [r2, 0, r2, 0])
        assert_array_almost_equal(rotation_from_z(np.array([0, 1, 0])), [r2, -r2, 0, 0])
        assert_array_almost_equal(rotation_from_z(np.array([1, 1, 0])), [r2, -0.5, 0.5, 0])
        assert_array_almost_equal(rotation_from_z(np.array([0, 0, 1])), [1, 0, 0, 0])

    def test_box_positions_in(self):
        b = Box((0, 2, 4), (2, 2, 2))
        # check that non-array call works
        assert b.are_positions_inside((1, 3, 5))
        assert not b.are_positions_inside((-1, 3, 5))
        b.xp.testing.assert_array_equal(b.are_positions_inside(
            [
                (1, 3, 5), (0.5, 2.5, 5.5),
                (0, 2, 4), (2, 4, 6), (0, 3, 5), (1, 2, 6),
                (-1, 3, 5), (3, 3, 5), (1, 0, 5), (1, 5, 5), (1, 3, 2), (1, 3, 9),
                (10, -10, 10), (0, 0, 0)]),
            b.xp.asarray([1, 1,  # in the box
                          1, 1, 1, 1,  # on the surface
                          0, 0, 0, 0, 0, 0,  # far on one axis
                          0, 0]))  # far on all axes

    def test_sphere_positions_in(self):
        s = Sphere((2, 0, 0), 1)

        # check that non-array call works
        assert s.are_positions_inside((2, 0, 0))
        assert not s.are_positions_inside((2.8, -0.8, 0.8))

        s.xp.testing.assert_array_equal(s.are_positions_inside(
            s.xp.asarray([(2, 0, 0), (2.3, 0.2, -0.3),
                      (1, 0, 0), (3, 0, 0), (2, 1, 0), (2, -1, 0), (2, 0, 1), (2, 0, -1),
                      (2, 0, -2), (1, 1, 0), (4, 0, 0),
                      (3, 4, 5), (3, -4, 5),
                      (2.5, 0.5, -0.5), (2.8, -0.8, 0.8)])),
            s.xp.asarray([1, 1,  # inside the sphere
                          1, 1, 1, 1, 1, 1,  # on the surface
                          0, 0, 0,  # far on one axis
                          0, 0,  # far on all axes
                          1, 0]))  # on the diagonal

    def test_cylinder_positions_in(self):
        c = Cylinder((2, 2, -2), (5, 2, 2), 5)

        # check that non-array call works
        assert c.are_positions_inside((3, 2, 0))
        assert not c.are_positions_inside((3, 10, 0))

        # assert c.are_positions_inside((-2.0, 2, 1))  - does not work without exact floating point
        # assert c.are_positions_inside((6.0, 2, -5)) - does not work without exact floating point
        # assert c.are_positions_inside((1, 2, 5)) - does not work without exact floating point

        c.xp.testing.assert_array_equal(c.are_positions_inside(np.array([
            (3, 2, 0), (4, 1, 1),
            (3, 10, 0), (3, -10, 0), (3, 2, 10), (3, 2, -10), (10, 2, 0), (-10, 2, 0),
            (-1.9, 2, 1), (-2.1, 2, 1), (-2.0, 2, 0.9), (-2.0, 2, 1.1), (-2.0, 1.9, 1), (-2.0, 2.1, 1),
            (6, 2, -4.9), (6, 2, -5.1), (6.1, 2, -5), (5.9, 2, -5), (6, 1.9, -5), (6, 2.1, -5),
            (1, 2, 4.9), (1, 2, 5.1), (1.1, 2, 5), (0.9, 2, 5), (1, 1.9, 5), (1, 2.1, 5)])),
            c.xp.asarray([1, 1,  # inside
                          0, 0, 0, 0, 0, 0,  # far away
                          1, 0, 0, 0, 0, 0,  # corners of the projection on y=2
                          1, 0, 0, 0, 0, 0,
                          1, 0, 0, 0, 0, 0]))

    def test_tube_positions_in(self):
        t = Tube((2, 2, -2), (5, 2, 2), 2.5, 5)
        assert not t.are_positions_inside((3, 2, 0))
        assert t.are_positions_inside((0, 2, 1))

        # assert c.are_positions_inside((-2.0, 2, 1))  - does not work without exact floating point
        # assert c.are_positions_inside((6.0, 2, -5)) - does not work without exact floating point
        # assert c.are_positions_inside((1, 2, 5)) - does not work without exact floating point

        t.xp.testing.assert_array_equal(t.are_positions_inside(np.array([
            (3, 2, 0), (4, 1, 1),
            (0, 2, 1), (2, 2, 4), (5, 2, -3), (7, 2, 0), (3, 6, 0), (3, -1, 0),
            (3, 10, 0), (3, -10, 0), (3, 2, 10), (3, 2, -10), (10, 2, 0), (-10, 2, 0),
            (-1.9, 2, 1), (-2.1, 2, 1), (-2.0, 2, 0.9), (-2.0, 2, 1.1), (-2.0, 1.9, 1), (-2.0, 2.1, 1),
            (6, 2, -4.9), (6, 2, -5.1), (6.1, 2, -5), (5.9, 2, -5), (6, 1.9, -5), (6, 2.1, -5),
            (1, 2, 4.9), (1, 2, 5.1), (1.1, 2, 5), (0.9, 2, 5), (1, 1.9, 5), (1, 2.1, 5)])),
            t.xp.asarray([0, 0,  # inside innner cylinder
                          1, 1, 1, 1, 1, 1,
                          0, 0, 0, 0, 0, 0,  # far away
                          1, 0, 0, 0, 0, 0,  # corners of the projection on y=2
                          1, 0, 0, 0, 0, 0,
                          1, 0, 0, 0, 0, 0]))

    def test_generate_positions(self):
        shape = Box()
        num_points = 500000
        decimals = 2
        points = shape.generate_uniform_random_posititons(RandomState(0), num_points)
        assert shape.are_positions_inside(points).all()
        assert_array_almost_equal(points.mean(axis=0), (0.5, 0.5, 0.5), decimals)
        assert_array_almost_equal(np.median(points, axis=0), (0.5, 0.5, 0.5), decimals)
        assert_array_almost_equal(points.std(axis=0), (1 / sqrt(12), 1 / sqrt(12), 1 / sqrt(12)), decimals)
        assert_array_almost_equal(points.min(axis=0), (0, 0, 0), decimals)
        assert_array_almost_equal(points.max(axis=0), (1, 1, 1), decimals)
        assert_array_almost_equal(np.cov(points.transpose()), [[1 / 12, 0, 0],
                                                               [0, 1 / 12, 0],
                                                               [0, 0, 1 / 12]], decimals)
        shape = Cylinder()
        points = shape.generate_uniform_random_posititons(RandomState(0), num_points)
        assert shape.are_positions_inside(points).all()
        assert_array_almost_equal(points.mean(axis=0), (0.5, 0, 0), decimals)
        assert_array_almost_equal(np.median(points, axis=0), (0.5, 0, 0), decimals)
        assert_array_almost_equal(points.std(axis=0), (1 / sqrt(12), .5, .5), decimals)
        assert_array_almost_equal(points.min(axis=0), (0, -1, -1), decimals)
        assert_array_almost_equal(points.max(axis=0), (1, 1, 1), decimals)
        print(np.cov(points.transpose()))
        assert_array_almost_equal(np.cov(points.transpose()), [[1 / 12, 0, 0],
                                                               [0, 1 / 4, 0],
                                                               [0, 0, 1 / 4]], decimals)

        shape = Cylinder((0, 0, 0), (0, 0, 1), 1)
        points = shape.generate_uniform_random_posititons(RandomState(0), num_points)
        assert shape.are_positions_inside(points).all()
        assert_array_almost_equal(points.mean(axis=0), (0, 0, 0.5), decimals)
        assert_array_almost_equal(np.median(points, axis=0), (0, 0, 0.5), decimals)
        assert_array_almost_equal(points.std(axis=0), (.5, .5, 1 / sqrt(12)), decimals)
        assert_array_almost_equal(points.min(axis=0), (-1, -1, 0), decimals)
        assert_array_almost_equal(points.max(axis=0), (1, 1, 1), decimals)
        print(np.cov(points.transpose()))
        assert_array_almost_equal(np.cov(points.transpose()), [[1 / 4, 0, 0],
                                                               [0, 1 / 4, 0],
                                                               [0, 0, 1 / 12]], decimals)

        shape = Tube()
        points = shape.generate_uniform_random_posititons(RandomState(0), num_points)
        assert shape.are_positions_inside(points).all()
        assert_array_almost_equal(points.mean(axis=0), (0.5, 0, 0), decimals)
        assert_array_almost_equal(np.median(points, axis=0), (0.5, 0, 0), decimals)
        assert_array_almost_equal(points.std(axis=0), (1 / sqrt(12), sqrt(1.5), sqrt(1.5)), decimals)
        assert_array_almost_equal(points.min(axis=0), (0, -2, -2), decimals)
        assert_array_almost_equal(points.max(axis=0), (1, 2, 2), decimals)
        print(np.cov(points.transpose()))
        assert_array_almost_equal(np.cov(points.transpose()), [[1 / 12, 0, 0],
                                                               [0, 1.5, 0],
                                                               [0, 0, 1.5]], decimals)

        shape = Sphere()
        points = shape.generate_uniform_random_posititons(RandomState(0), num_points)
        assert shape.are_positions_inside(points).all()
        assert_array_almost_equal(points.mean(axis=0), (0, 0, 0), decimals)
        assert_array_almost_equal(np.median(points, axis=0), (0, 0, 0), decimals)
        assert_array_almost_equal(points.std(axis=0), (sqrt(.2), sqrt(.2), sqrt(.2)), decimals)
        assert_array_almost_equal(points.min(axis=0), (-1, -1, -1), decimals)
        assert_array_almost_equal(points.max(axis=0), (1, 1, 1), decimals)
        print(np.cov(points.transpose()))
        assert_array_almost_equal(np.cov(points.transpose()), [[.2, 0, 0],
                                                               [0, .2, 0],
                                                               [0, 0, .2]], decimals)
