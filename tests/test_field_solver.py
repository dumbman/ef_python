import numpy as np
from numpy.testing import assert_array_equal, assert_allclose
from scipy.sparse import csr_matrix

from ef.config.components import BoundaryConditionsConf, SpatialMeshConf
from ef.config.components import Box
from ef.field.solvers.pyamg import FieldSolverPyamg as FieldSolver
from ef.inner_region import InnerRegion


class TestFieldSolver:

    def test_global_index(self):
        double_index = FieldSolver.double_index(np.array((9, 10, 6)))
        for i in range(7):
            for j in range(8):
                for k in range(4):
                    n = i + j * 7 + k * 7 * 8
                    assert tuple(double_index[n]) == (n, i + 1, j + 1, k + 1)
        assert_array_equal(FieldSolver.double_index(np.array((4, 5, 3))), [(0, 1, 1, 1),
                                                                           (1, 2, 1, 1),
                                                                           (2, 1, 2, 1),
                                                                           (3, 2, 2, 1),
                                                                           (4, 1, 3, 1),
                                                                           (5, 2, 3, 1)])

    def test_generate_nodes_in_regions(self):
        mesh = SpatialMeshConf((4, 6, 9), (1, 2, 3)).make(BoundaryConditionsConf())
        solver = FieldSolver(mesh, [])
        inner_regions = [InnerRegion('test', Box((1, 2, 3), (1, 2, 3)), 3)]
        nodes, potential = solver.generate_nodes_in_regions(inner_regions)
        assert_array_equal(nodes, [0, 1, 3, 4, 6, 7, 9, 10])
        assert_array_equal(potential, [3, 3, 3, 3, 3, 3, 3, 3])

    def test_init_rhs(self):
        mesh = SpatialMeshConf((4, 3, 3)).make(BoundaryConditionsConf())
        solver = FieldSolver(mesh, [])
        solver.init_rhs_vector_in_full_domain()
        assert_array_equal(solver.rhs, np.zeros(3 * 2 * 2))
        del solver

        mesh = SpatialMeshConf((4, 3, 3)).make(BoundaryConditionsConf(-2))
        solver = FieldSolver(mesh, [])
        solver.init_rhs_vector_in_full_domain()
        assert_array_equal(solver.rhs, [6, 4, 6, 6, 4, 6, 6, 4, 6, 6, 4, 6])  # what
        del solver

        mesh = SpatialMeshConf((4, 4, 5)).make(BoundaryConditionsConf(-2))
        solver = FieldSolver(mesh, [])
        solver.init_rhs_vector_in_full_domain()
        assert_array_equal(solver.rhs, [6, 4, 6, 4, 2, 4, 6, 4, 6,
                                        4, 2, 4, 2, 0, 2, 4, 2, 4,
                                        4, 2, 4, 2, 0, 2, 4, 2, 4,
                                        6, 4, 6, 4, 2, 4, 6, 4, 6])  # what
        del solver

        mesh = SpatialMeshConf((8, 12, 5), (2, 3, 1)).make(BoundaryConditionsConf(-1))
        solver = FieldSolver(mesh, [])
        solver.init_rhs_vector_in_full_domain()
        assert_array_equal(solver.rhs, [49, 40, 49, 45, 36, 45, 49, 40, 49,
                                        13, 4, 13, 9, 0, 9, 13, 4, 13,
                                        13, 4, 13, 9, 0, 9, 13, 4, 13,
                                        49, 40, 49, 45, 36, 45, 49, 40, 49])
        del solver

        mesh = SpatialMeshConf((4, 6, 9), (1, 2, 3)).make(BoundaryConditionsConf())
        solver = FieldSolver(mesh, [])
        mesh.charge_density.data = np.array([[[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
                                             [[0, 0, 0, 0], [0, 1, 2, 0], [0, -1, 0, 0], [0, 0, 0, 0]],
                                             [[0, 0, 0, 0], [0, 3, 4, 0], [0, 0, -1, 0], [0, 0, 0, 0]],
                                             [[0, 0, 0, 0], [0, 5, 6, 0], [0, -1, 0, 0], [0, 0, 0, 0]],
                                             [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]])
        solver.init_rhs_vector_in_full_domain()
        assert_allclose(solver.rhs, -np.array([1, 3, 5, -1, 0, -1, 2, 4, 6, 0, -1, 0]) * np.pi * 4 * 36)
        del solver

        mesh = SpatialMeshConf((4, 6, 9), (1, 2, 3)).make(BoundaryConditionsConf())
        solver = FieldSolver(mesh, [])
        nodep = solver.generate_nodes_in_regions([InnerRegion('test', Box((1, 2, 3), (1, 2, 3)), 3)])
        solver.nodes_in_regions, solver.potential_in_regions = nodep
        solver.init_rhs_vector()
        assert_array_equal(solver.rhs, [3, 3, 0, 3, 3, 0, 3, 3, 0, 3, 3, 0])

    def test_zero_nondiag_inside_objects(self):
        mesh = SpatialMeshConf((4, 6, 9), (1, 2, 3)).make(BoundaryConditionsConf())
        solver = FieldSolver(mesh, [InnerRegion('test', Box((1, 2, 3), (1, 2, 3)), 3)])

        a = csr_matrix(np.full((12, 12), 2))
        assert_array_equal(a.toarray(), [[2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
                                         [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
                                         [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
                                         [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
                                         [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
                                         [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
                                         [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
                                         [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
                                         [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
                                         [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
                                         [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
                                         [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]])
        result = solver.zero_nondiag_for_nodes_inside_objects(a)
        assert_array_equal(result.toarray(), [[1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                                              [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                                              [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
                                              [0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0],
                                              [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
                                              [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
                                              [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0],
                                              [0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
                                              [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
                                              [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0],
                                              [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0],
                                              [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]])

        # TODO: check algorithm if on-diagonal zeros should turn into ones
        a = csr_matrix(np.array([[4, 0, 3, 0, 0, 0, 0, 2, 0, 0, 0, 0],
                                 [0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 0, 0],
                                 [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                                 [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                                 [0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0],
                                 [0, 0, 2, 0, 0, 3, 0, 0, 0, 0, 0, 0],
                                 [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                                 [0, 0, 2, 0, 0, 0, 0, 0, 0, 1, 0, 0],
                                 [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3],
                                 [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                                 [0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 6, 0],
                                 [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]]))
        result = solver.zero_nondiag_for_nodes_inside_objects(a)
        assert_array_equal(result.toarray(), [[1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                                              [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                                              [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                                              [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                                              [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
                                              [0, 0, 2, 0, 0, 3, 0, 0, 0, 0, 0, 0],
                                              [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                                              [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                                              [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3],
                                              [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                                              [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0],
                                              [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]])

    def test_d2dx2(self):
        a = FieldSolver.construct_d2dx2_in_3d(3, 2, 2).toarray()
        assert_array_equal(a, [[-2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                               [1, -2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                               [0, 1, -2, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                               [0, 0, 0, -2, 1, 0, 0, 0, 0, 0, 0, 0],
                               [0, 0, 0, 1, -2, 1, 0, 0, 0, 0, 0, 0],
                               [0, 0, 0, 0, 1, -2, 0, 0, 0, 0, 0, 0],
                               [0, 0, 0, 0, 0, 0, -2, 1, 0, 0, 0, 0],
                               [0, 0, 0, 0, 0, 0, 1, -2, 1, 0, 0, 0],
                               [0, 0, 0, 0, 0, 0, 0, 1, -2, 0, 0, 0],
                               [0, 0, 0, 0, 0, 0, 0, 0, 0, -2, 1, 0],
                               [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, -2, 1],
                               [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, -2]])
        a = FieldSolver.construct_d2dx2_in_3d(3, 2, 1).toarray()
        assert_array_equal(a, [[-2, 1, 0, 0, 0, 0],
                               [1, -2, 1, 0, 0, 0],
                               [0, 1, -2, 0, 0, 0],
                               [0, 0, 0, -2, 1, 0],
                               [0, 0, 0, 1, -2, 1],
                               [0, 0, 0, 0, 1, -2]])

    def test_d2dy2(self):
        a = FieldSolver.construct_d2dy2_in_3d(3, 2, 2).toarray()
        assert_array_equal(a, [[-2, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0],
                               [0, -2, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
                               [0, 0, -2, 0, 0, 1, 0, 0, 0, 0, 0, 0],
                               [1, 0, 0, -2, 0, 0, 0, 0, 0, 0, 0, 0],
                               [0, 1, 0, 0, -2, 0, 0, 0, 0, 0, 0, 0],
                               [0, 0, 1, 0, 0, -2, 0, 0, 0, 0, 0, 0],
                               [0, 0, 0, 0, 0, 0, -2, 0, 0, 1, 0, 0],
                               [0, 0, 0, 0, 0, 0, 0, -2, 0, 0, 1, 0],
                               [0, 0, 0, 0, 0, 0, 0, 0, -2, 0, 0, 1],
                               [0, 0, 0, 0, 0, 0, 1, 0, 0, -2, 0, 0],
                               [0, 0, 0, 0, 0, 0, 0, 1, 0, 0, -2, 0],
                               [0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, -2]])
        a = FieldSolver.construct_d2dy2_in_3d(3, 2, 1).toarray()
        assert_array_equal(a, [[-2, 0, 0, 1, 0, 0],
                               [0, -2, 0, 0, 1, 0],
                               [0, 0, -2, 0, 0, 1],
                               [1, 0, 0, -2, 0, 0],
                               [0, 1, 0, 0, -2, 0],
                               [0, 0, 1, 0, 0, -2]])

    def test_d2dz2(self):
        a = FieldSolver.construct_d2dz2_in_3d(3, 2, 2).toarray()
        assert_array_equal(a, [[-2, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0],
                               [0, -2, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
                               [0, 0, -2, 0, 0, 0, 0, 0, 1, 0, 0, 0],
                               [0, 0, 0, -2, 0, 0, 0, 0, 0, 1, 0, 0],
                               [0, 0, 0, 0, -2, 0, 0, 0, 0, 0, 1, 0],
                               [0, 0, 0, 0, 0, -2, 0, 0, 0, 0, 0, 1],
                               [1, 0, 0, 0, 0, 0, -2, 0, 0, 0, 0, 0],
                               [0, 1, 0, 0, 0, 0, 0, -2, 0, 0, 0, 0],
                               [0, 0, 1, 0, 0, 0, 0, 0, -2, 0, 0, 0],
                               [0, 0, 0, 1, 0, 0, 0, 0, 0, -2, 0, 0],
                               [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, -2, 0],
                               [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, -2]])
        a = FieldSolver.construct_d2dz2_in_3d(3, 2, 1).toarray()
        assert_array_equal(a, [[-2, 0, 0, 0, 0, 0],
                               [0, -2, 0, 0, 0, 0],
                               [0, 0, -2, 0, 0, 0],
                               [0, 0, 0, -2, 0, 0],
                               [0, 0, 0, 0, -2, 0],
                               [0, 0, 0, 0, 0, -2]])

    def test_construct_equation_matrix(self):
        mesh = SpatialMeshConf((4, 6, 9), (1, 2, 3)).make(BoundaryConditionsConf())
        solver = FieldSolver(mesh, [])
        solver.construct_equation_matrix()
        d = -2 * (2 * 2 * 3 * 3 + 3 * 3 + 2 * 2)
        x = 2 * 2 * 3 * 3
        y = 3 * 3
        z = 2 * 2
        assert_array_equal(solver.A.toarray(), [[d, x, 0, y, 0, 0, z, 0, 0, 0, 0, 0],
                                                [x, d, x, 0, y, 0, 0, z, 0, 0, 0, 0],
                                                [0, x, d, 0, 0, y, 0, 0, z, 0, 0, 0],
                                                [y, 0, 0, d, x, 0, 0, 0, 0, z, 0, 0],
                                                [0, y, 0, x, d, x, 0, 0, 0, 0, z, 0],
                                                [0, 0, y, 0, x, d, 0, 0, 0, 0, 0, z],
                                                [z, 0, 0, 0, 0, 0, d, x, 0, y, 0, 0],
                                                [0, z, 0, 0, 0, 0, x, d, x, 0, y, 0],
                                                [0, 0, z, 0, 0, 0, 0, x, d, 0, 0, y],
                                                [0, 0, 0, z, 0, 0, y, 0, 0, d, x, 0],
                                                [0, 0, 0, 0, z, 0, 0, y, 0, x, d, x],
                                                [0, 0, 0, 0, 0, z, 0, 0, y, 0, x, d]])

    def test_transfer_solution_to_spat_mesh(self):
        mesh = SpatialMeshConf((4, 6, 9), (1, 2, 3)).make(BoundaryConditionsConf())
        solver = FieldSolver(mesh, [])
        solver.phi_vec = np.array(range(1, 3 * 2 * 2 + 1))
        solver.transfer_solution_to_spat_mesh()
        assert_array_equal(mesh.potential.data[1:-1, 1:-1, 1:-1], [[[1, 7], [4, 10]],
                                                                   [[2, 8], [5, 11]],
                                                                   [[3, 9], [6, 12]]])

        assert_array_equal(mesh.potential.data, [
            [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
            [[0, 0, 0, 0], [0, 1, 7, 0], [0, 4, 10, 0], [0, 0, 0, 0]],
            [[0, 0, 0, 0], [0, 2, 8, 0], [0, 5, 11, 0], [0, 0, 0, 0]],
            [[0, 0, 0, 0], [0, 3, 9, 0], [0, 6, 12, 0], [0, 0, 0, 0]],
            [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]])
