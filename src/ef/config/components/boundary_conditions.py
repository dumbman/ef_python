__all__ = ["BoundaryConditionsConf", "BoundaryConditionsSection"]

from collections import namedtuple

import numpy as np

from ef.config.component import ConfigComponent
from ef.config.section import ConfigSection


class BoundaryConditionsConf(ConfigComponent):
    def __init__(self, right=None, left=None, bottom=None, top=None, near=None, far=None):
        args = [right, left, bottom, top, near, far]
        provided_args = [float(x) for x in args if x is not None]
        if len(provided_args) == 0:
            provided_args = [0.]
        if len(provided_args) == 1:
            self.right = self.left = self.bottom = self.top = self.near = self.far = provided_args[0]
        elif len(provided_args) == 6:
            self.right, self.left, self.bottom, self.top, self.near, self.far = provided_args
        else:
            raise ValueError("Wrong number of arguments to BoundaryConditions.__init__()", len(provided_args))

    @property
    def is_the_same_on_all_boundaries(self):
        return self.right == self.left == self.bottom == self.top == self.near == self.far

    def to_conf(self):
        return BoundaryConditionsSection(self.right, self.left, self.bottom, self.top, self.near, self.far)

    def visualize(self, visualizer, volume_size=(1, 1, 1)):
        visualizer.draw_box(np.array(volume_size, np.float), wireframe=True,
                            colors=visualizer.potential_mapper.to_rgba(self.right))
        # TODO: visualize non-uniform conditions


class BoundaryConditionsSection(ConfigSection):
    section = "BoundaryConditions"
    ContentTuple = namedtuple("BoundaryConditionsTuple",
                              ('boundary_phi_right', 'boundary_phi_left', 'boundary_phi_bottom',
                               'boundary_phi_top', 'boundary_phi_near', 'boundary_phi_far'))
    convert = ContentTuple(*[float] * 6)

    def make(self):
        return BoundaryConditionsConf(*self.content)
