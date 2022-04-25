import pytest

print("setting up")


@pytest.fixture(scope="session")
def tmpfile(tmpdir_factory):
    """Sets up a temporary file

    https://docs.pytest.org/en/latest/tmpdir.html#the-tmpdir-factory-fixture
    """

    def make(filename):
        fn = tmpdir_factory.mktemp("data").join(filename)
        return fn

    # fn = tmpdir_factory.mktemp("data").join(filename)
    return make
