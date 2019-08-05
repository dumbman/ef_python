import numpy as np

from ef.field import Field
from ef.inner_region import InnerRegion
from ef.meshgrid import MeshGrid
from ef.particle_array import ParticleArray
from ef.particle_interaction_model import Model
from ef.particle_source import ParticleSource
from ef.simulation import Simulation
from ef.spatial_mesh import SpatialMesh
from ef.time_grid import TimeGrid
from ef.util.array_on_grid import ArrayOnGrid


class Reader:
    @staticmethod
    def guess_h5_format(h5file):
        if 'SpatialMesh' in h5file:
            return 'cpp'
        elif 'history' in h5file:
            return 'history'
        elif 'spat_mesh' in h5file:
            return 'python'
        else:
            raise ValueError('Cannot guess hdf5 file format')

    @staticmethod
    def read_simulation(h5file):
        format_ = Reader.guess_h5_format(h5file)
        if format_ == 'cpp':
            return Reader.import_from_h5(h5file)
        elif format_ == 'python':
            sim = Simulation.load_h5(h5file)
        else:
            sim = Simulation.load_h5(h5file['simulation'])
        sim.particle_interaction_model = Model[sim.particle_interaction_model]
        return sim

    @staticmethod
    def import_from_h5(h5file):
        fields = [Field.import_h5(g) for g in h5file['ExternalFields'].values()]
        sources = [ParticleSource.import_h5(g) for g in h5file['ParticleSources'].values()]
        particles = [ParticleArray.import_h5(g) for g in h5file['ParticleSources'].values()]
        max_id = int(np.max([p.ids for p in particles], initial=-1))
        g = h5file['SpatialMesh']
        mesh = MeshGrid.import_h5(g)
        charge = ArrayOnGrid(mesh, (), np.reshape(g['charge_density'], mesh.n_nodes))
        potential = ArrayOnGrid(mesh, (), np.reshape(g['potential'], mesh.n_nodes))
        field = ArrayOnGrid(mesh, 3, np.moveaxis(
            np.array([np.reshape(g['electric_field_{}'.format(c)], mesh.n_nodes) for c in 'xyz']),
            0, -1))
        spat_mesh = SpatialMesh(mesh, charge, potential, field)
        return Simulation(
            time_grid=TimeGrid.import_h5(h5file['TimeGrid']),
            spat_mesh=spat_mesh,
            inner_regions=[InnerRegion.import_h5(g) for g in h5file['InnerRegions'].values()],
            electric_fields=[f for f in fields if f.electric_or_magnetic == 'electric'],
            magnetic_fields=[f for f in fields if f.electric_or_magnetic == 'magnetic'],
            particle_interaction_model=Model[
                h5file['ParticleInteractionModel'].attrs['particle_interaction_model'].decode('utf8')
            ],
            particle_sources=sources, particle_arrays=particles, max_id=max_id
        )
