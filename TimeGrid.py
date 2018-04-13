import logging
from math import ceil


class TimeGrid:
    def __init__(self, total_time, time_step_size, time_save_step):
        if total_time <= 0:
            raise ValueError()
        if time_save_step < time_step_size:
            raise ValueError()
        if time_step_size <= 0:
            raise ValueError()
        if time_step_size > total_time:
            raise ValueError()
        self.total_time = total_time
        self.total_nodes = ceil(total_time / time_step_size) + 1
        self.time_step_size = self.total_time / (self.total_nodes - 1)
        if self.time_step_size != time_step_size:
            logging.warning("Reducing time step to {:.3E} from {:.3E} "
                            "to fit a whole number of cells."
                            .format(self.time_step_size, time_step_size))
        self.time_save_step = int(time_save_step / self.time_step_size) * self.time_step_size
        if self.time_save_step != time_save_step:
            logging.warning("Reducing save time step to {:.3E} from {:.3E} "
                            "to fit a whole number of cells."
                            .format(self.time_save_step, time_save_step))
        self.node_to_save = int(self.time_save_step / self.time_step_size)  # what?
        self.current_time = 0.0
        self.current_node = 0

    @classmethod
    def init_from_config(cls, conf):
        total_time = conf["TimeGrid"].getfloat("total_time")
        time_step_size = conf["TimeGrid"].getfloat("time_step_size")
        time_save_step = conf["TimeGrid"].getfloat("time_save_step")
        TimeGrid.mark_timegrid_sec_as_used(conf)
        return cls(total_time, time_step_size, time_save_step)

    @staticmethod
    def mark_timegrid_sec_as_used(conf):
        # For now simply mark sections as 'used' instead of removing them.
        conf["TimeGrid"]["used"] = "True"

    @classmethod
    def init_from_h5(cls, h5group):
        total_time = h5group.attrs["total_time"]
        time_step_size = h5group.attrs["time_step_size"]
        time_save_step = h5group.attrs["time_save_step"]
        grid = cls(total_time, time_step_size, time_save_step)
        grid.current_time = h5group.attrs["current_time"]
        grid.total_nodes = h5group.attrs["total_nodes"]
        grid.current_node = h5group.attrs["current_node"]
        grid.node_to_save = h5group.attrs["node_to_save"]
        return grid

    def update_to_next_step(self):
        self.current_node += 1
        self.current_time += self.time_step_size

    def print(self):
        print("### TimeGrid:")
        print("Total time = {:.3E}".format(self.total_time))
        print("Current time = {:.3E}".format(self.current_time))
        print("Time step size = {:.3E}".format(self.time_step_size))
        print("Time save step = {:.3E}".format(self.time_save_step))
        print("Total nodes = {:d}".format(self.total_nodes))
        print("Current node = {:d}".format(self.current_node))
        print("Node to save = {:d}".format(self.node_to_save))

    def write_to_file(self, h5file):
        groupname = "/TimeGrid"
        h5group = h5file.create_group(groupname)
        h5group.attrs.create("total_time", self.total_time)
        h5group.attrs.create("current_time", self.current_time)
        h5group.attrs.create("time_step_size", self.time_step_size)
        h5group.attrs.create("time_save_step", self.time_save_step)
        h5group.attrs.create("total_nodes", self.total_nodes)
        h5group.attrs.create("current_node", self.current_node)
        h5group.attrs.create("node_to_save", self.node_to_save)
