import pytest

@pytest.fixture
def dummy_fixture():
    return True

def test_dummy(dummy_fixture):
    assert dummy_fixture
