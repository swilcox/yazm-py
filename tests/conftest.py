import pytest

from yazm.zmachine import ZMachine

from ._sample_data import ZSAMPLE_DATA


@pytest.fixture
def sample_zmachine():
    """Create a ZMachine instance from the bundled minizork sample data."""
    return ZMachine(ZSAMPLE_DATA)
