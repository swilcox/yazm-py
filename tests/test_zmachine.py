from yazm.zmachine import ZMachine
from ._sample_data import ZSAMPLE_DATA


def test_zmachine_init():
    zmachine = ZMachine(ZSAMPLE_DATA)
    assert(len(zmachine.dictionary.keys()) == 536)
    assert([k for k in zmachine.dictionary.keys()][-1] == 'zork')
