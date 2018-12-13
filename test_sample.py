import pytest
from Vec3d import Vec3d

def test():
    vec=Vec3d(0,0,0)
    length=vec.length()
    assert length == 0

