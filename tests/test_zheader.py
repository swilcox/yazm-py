from yazm.zmachine import ZMachine
from ._sample_data import ZSAMPLE_DATA


def test_header():
    zmachine = ZMachine(ZSAMPLE_DATA)
    assert(zmachine.header.version == 3)
    assert(zmachine.header.release == 34)
    #TODO: all things header related
