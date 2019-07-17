import numpy as np
import pyamg
import scipy.sparse
import scipy.sparse.linalg


class FieldSolver:
    def __init__(self, spat_mesh, inner_regions):
        if inner_regions:
            print("WARNING: field-solver: inner region support is untested")
            print("WARNING: proceed with caution")
        self._double_index = self.double_index(spat_mesh.n_nodes)
        nrows = (spat_mesh.n_nodes - 2).prod()
        self.A = self.construct_equation_matrix(spat_mesh, inner_regions)
        self.phi_vec = np.empty(nrows, dtype='f')
        self.rhs = np.empty_like(self.phi_vec)
        self.create_solver_and_preconditioner()

    def construct_equation_matrix(self, spat_mesh, inner_regions):
        nx, ny, nz = spat_mesh.n_nodes - 2
        cx, cy, cz = spat_mesh.cell ** 2
        dx, dy, dz = cy * cz, cx * cz, cx * cy
        matrix = dx * self.construct_d2dx2_in_3d(nx, ny, nz) + \
                 dy * self.construct_d2dy2_in_3d(nx, ny, nz) + \
                 dz * self.construct_d2dz2_in_3d(nx, ny, nz)
        return self.zero_nondiag_for_nodes_inside_objects(matrix, spat_mesh, inner_regions)

    @staticmethod
    def construct_d2dx2_in_3d(nx, ny, nz):
        diag_offset = 1
        block_size = nx
        block = scipy.sparse.diags([1.0, -2.0, 1.0], [-diag_offset, 0, diag_offset], shape=(block_size, block_size),
                                   format='coo')
        big_block = scipy.sparse.block_diag([block] * nz, format='coo')
        return scipy.sparse.block_diag([big_block] * ny, format='csr')

    @staticmethod
    def construct_d2dy2_in_3d(nx, ny, nz):
        diag_offset = nx
        block_size = nx * ny
        block = scipy.sparse.diags([1.0, -2.0, 1.0], [-diag_offset, 0, diag_offset], shape=(block_size, block_size),
                                   format='coo')
        return scipy.sparse.block_diag([block] * nz, format='csr')

    @staticmethod
    def construct_d2dz2_in_3d(nx, ny, nz):
        diag_offset = nx * ny
        block_size = nx * ny * nz
        return scipy.sparse.diags([1.0, -2.0, 1.0], [-diag_offset, 0, diag_offset], shape=(block_size, block_size),
                                  format='csr')

    def zero_nondiag_for_nodes_inside_objects(self, matrix, mesh, inner_regions):
        for ir in inner_regions:
            ijk = self._double_index[:, 1:]
            n = self._double_index[:, 0]
            xyz = mesh.cell * ijk
            mask = ir.check_if_points_inside(xyz)
            n = n[mask]
            for i in n:
                csr_row_start = matrix.indptr[i]
                csr_row_end = matrix.indptr[i + 1]
                for t in range(csr_row_start, csr_row_end):
                    if matrix.indices[t] != i:
                        matrix.data[t] = 0
                    else:
                        matrix.data[t] = 1
        return matrix

    def create_solver_and_preconditioner(self):
        self.maxiter = 1000
        self.tol = 1e-10
        self._solver = pyamg.ruge_stuben_solver(self.A)
        # abstol = 0
        # verbose = true
        # monitor(rhs, iteration_limit, rtol, abstol, verbose)
        # precond(A.num_rows, A.num_rows)

    def eval_potential(self, spat_mesh, inner_regions):
        self.solve_poisson_eqn(spat_mesh, inner_regions)

    def solve_poisson_eqn(self, spat_mesh, inner_regions):
        self.init_rhs_vector(spat_mesh, inner_regions)
        self.phi_vec = self._solver.solve(self.rhs, x0=self.phi_vec, tol=self.tol, maxiter=self.maxiter)
        self.transfer_solution_to_spat_mesh(spat_mesh)

    def init_rhs_vector(self, spat_mesh, inner_regions):
        self.init_rhs_vector_in_full_domain(spat_mesh)
        self.set_rhs_for_nodes_inside_objects(spat_mesh, inner_regions)

    def init_rhs_vector_in_full_domain(self, spat_mesh):
        m = spat_mesh
        rhs = -4 * np.pi * m.cell.prod() ** 2 * m.charge_density[1:-1, 1:-1, 1:-1]
        dx, dy, dz = m.cell
        rhs[0] -= dy * dy * dz * dz * m.potential[0, 1:-1, 1:-1]
        rhs[-1] -= dy * dy * dz * dz * m.potential[-1, 1:-1, 1:-1]
        rhs[:, 0] -= dx * dx * dz * dz * m.potential[1:-1, 0, 1:-1]
        rhs[:, -1] -= dx * dx * dz * dz * m.potential[1:-1, -1, 1:-1]
        rhs[:, :, 0] -= dx * dx * dy * dy * m.potential[1:-1, 1:-1, 0]
        rhs[:, :, -1] -= dx * dx * dy * dy * m.potential[1:-1, 1:-1, -1]
        self.rhs = rhs.ravel('F')

    def set_rhs_for_nodes_inside_objects(self, spat_mesh, inner_regions):
        for ir in inner_regions:
            ijk = self._double_index[:, 1:]
            n = self._double_index[:, 0]
            xyz = spat_mesh.cell * ijk
            mask = ir.check_if_points_inside(xyz)
            self.rhs[n[mask]] = ir.potential

    def transfer_solution_to_spat_mesh(self, spat_mesh):
        spat_mesh.potential[1:-1, 1:-1, 1:-1] = self.phi_vec.reshape(spat_mesh.n_nodes - 2, order='F')

    @staticmethod
    def eval_fields_from_potential(spat_mesh):
        e = -np.stack(np.gradient(spat_mesh.potential, *spat_mesh.cell), -1)
        spat_mesh.electric_field = e

    @staticmethod
    def double_index(n_nodes):
        nx, ny, nz = n_nodes - 2
        return np.array([(i + j * nx + k * nx * ny, i + 1, j + 1, k + 1)
                         for k in range(nz) for j in range(ny) for i in range(nx)])
