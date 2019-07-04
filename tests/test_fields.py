import numpy as np
from numpy.testing import assert_array_almost_equal, assert_array_equal

from ef.field.expression import FieldExpression
from ef.field.on_grid import FieldOnGrid
from ef.field.uniform import FieldUniform, FieldZero


class TestFields:

    def test_uniform(self):
        f = FieldUniform('u1', 'electric', np.array((3.14, 2.7, -0.5)))
        assert_array_equal(f.get_at_points((1, 2, 3), 0.), (3.14, 2.7, -0.5))
        assert_array_equal(f.get_at_points((1, 2, 3), 5.), (3.14, 2.7, -0.5))
        assert_array_equal(f.get_at_points((3, 2, 1), 5.), (3.14, 2.7, -0.5))

    def test_zero(self):
        f = FieldZero('z', 'magnetic')
        assert_array_equal(f.get_at_points((1, 2, 3), 0.), (0, 0, 0))
        assert_array_equal(f.get_at_points((1, 2, 3), 5.), (0, 0, 0))
        assert_array_equal(f.get_at_points((3, 2, 1), 5.), (0, 0, 0))

    def test_expression(self):
        f = FieldExpression('e1', 'electric', '-1+t', 'x*y-z', 'x+y*z')
        assert_array_equal(f.get_at_points((1, 2, 3), 0.), (-1, -1, 7))
        assert_array_equal(f.get_at_points((1, 2, 3), 5.), (4, -1, 7))
        assert_array_equal(f.get_at_points((3, 2, 1), 5.), (4, 5, 5))

    def test_from_file(self):
        f = FieldOnGrid('f1', 'electric', 'tests/test_field.csv')
        assert_array_equal(f.get_at_points([(0, 0, 0), (1, 1, 1), (1, 0, 1), (.5, .5, .5)], 0),
                           [(1, 1, 1), (-1, -1, -1), (3, 2, 1), (1, 1, 1)])
        assert_array_equal(f.get_at_points([(0, 0, 0), (1, 1, 1), (1, 0, 1), (.5, .5, .5)], 10.),
                           [(1, 1, 1), (-1, -1, -1), (3, 2, 1), (1, 1, 1)])
        assert_array_almost_equal(f.get_at_points([(.5, 1., .3), (0, .5, .7)], 5), [(0., .5, 1.), (1, 1.5, 2)])
        assert_array_equal(f.get_at_points([(-1, 1., .3), (1, 1, 10)], 3), [(0, 0, 0), (0, 0, 0)])
