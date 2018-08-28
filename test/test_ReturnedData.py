import pytest

from viresclient._data_handling import ReturnedData

SUPPORTED_FILETYPES = ('csv', 'cdf', 'nc')


def test_ReturnedData_setup():
    """Test setup of ReturnedData objects

    Enforcement of filetype as 'csv'/'cdf'/'nc' (lower case)
    """
    # CSV/CDF/NC should be converted to csv/cdf/nc
    for filetype in SUPPORTED_FILETYPES:
        retdata = ReturnedData(filetype=filetype.upper())
        assert retdata.filetype == filetype
        retdata = ReturnedData(filetype=filetype)
        assert retdata.filetype == filetype

    # The following should raise a TypeError:
    #  filetype must be csv/cdf/nc
    with pytest.raises(TypeError):
        retdata = ReturnedData(filetype='xyz')
    with pytest.raises(TypeError):
        retdata = ReturnedData(filetype=1)


def test_ReturnedData_saving(tmpfile):
    """Test saving of ReturnedData

    Writing files with extension checking
    Dealing correctly with overwrite or not
    """
    for filetype in SUPPORTED_FILETYPES:

        # Check that file name and extension checking is enforced
        retdata = ReturnedData(filetype=filetype)
        retdata._write_new_data(b'testtext')
        with pytest.raises(TypeError):
            retdata.to_file(1)
        with pytest.raises(TypeError):
            retdata.to_file(
                str(tmpfile("testfile.xyz"))
                )

        # Check that not overwriting and overwriting work right
        testfile = str(tmpfile('testfile.{}'.format(filetype)))
        retdata.to_file(testfile)
        # with pytest.raises(FileExistsError):  # not in py27
        with pytest.raises(Exception):
            retdata.to_file(
                testfile, overwrite=False
                )
        retdata.to_file(
            testfile, overwrite=True
            )
