from enum import Enum
from typing import Dict, Type, cast

import numpy as np
from h5py import Dataset, Group

from ef.util.data_class import DataClass
from ef.util.subclasses import Registered


class SerializableH5(DataClass, Registered, dont_register=True):
    def save_h5(self, h5group):
        h5group.attrs['class'] = self.class_key
        for k, v in self.dict.items():
            self._save_value(h5group, k, v)

    @staticmethod
    def load_h5(h5group: Group) -> 'SerializableH5':
        return cast('SerializableH5', SerializableH5.subclasses[h5group.attrs['class']]).load_h5_args(h5group)

    @classmethod
    def load_h5_args(cls, h5group):
        kwargs = {key: cls._load_value(value) for key, value in h5group.items()}
        kwargs.update(h5group.attrs)
        del kwargs['class']
        return cls(**kwargs)

    @classmethod
    def _save_value(cls, group, key, value):
        if isinstance(value, np.ndarray):
            group[key] = value
        elif isinstance(value, SerializableH5):
            value.save_h5(group.create_group(key))
        elif isinstance(value, list):
            subgroup = group.create_group(key)
            for i, v in enumerate(value):
                cls._save_value(subgroup, str(i), v)
        elif isinstance(value, Enum):
            group.attrs[key] = value.name
        else:
            group.attrs[key] = value

    @classmethod
    def _load_value(cls, value):
        if isinstance(value, Dataset):
            return np.array(value)
        elif isinstance(value, Group):
            try:
                return SerializableH5.load_h5(value)
            except KeyError as err:
                d = {k: cls._load_value(v) for k, v in value.items()}
                d.update(value.attrs)
                if d.keys() != {str(i) for i in range(len(d))}:
                    raise TypeError("Could not parse hdf5 group into SerializableH5", value) from err
            return [d[str(i)] for i in range(len(d.keys()))]
        else:
            raise TypeError("hdf5 group member of unexpected type found", value)
