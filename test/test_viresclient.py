import pytest
import os
import pandas as pd

from viresclient._data_handling import ReturnedData
from viresclient import ClientRequest
import viresclient

SUPPORTED_FILETYPES = ('csv', 'cdf')


def test_ReturnedData_setup():
    """Test the ReturnedData functionality

    Enforcement of filetype as csv/cdf, and data as bytes
    Writing files and dealing correctly with overwrite or not
    TODO: creation of dataframe
    """
    # CSV/CDF should be converted to csv/cdf
    retdata = ReturnedData(data=b'', filetype='CSV')
    assert retdata.filetype == 'csv'
    assert retdata.data == b''
    retdata = ReturnedData(data=b'', filetype='csv')
    assert retdata.filetype == 'csv'
    assert retdata.data == b''
    retdata = ReturnedData(data=b'', filetype='CDF')
    assert retdata.filetype == 'cdf'
    assert retdata.data == b''
    retdata = ReturnedData(data=b'', filetype='cdf')
    assert retdata.filetype == 'cdf'
    assert retdata.data == b''

    # The following should raise a TypeError:
    #  data must be a bytes,
    #  filetype must be csv/cdf
    with pytest.raises(TypeError):
        retdata = ReturnedData(data=b'', filetype='xyz')
    with pytest.raises(TypeError):
        retdata = ReturnedData(data=b'', filetype=1)
    with pytest.raises(TypeError):
        retdata = ReturnedData(data=1, filetype='CDF')
    with pytest.raises(TypeError):
        retdata = ReturnedData(data=1, filetype='xyz')


def test_ReturnedData_saving(tmpfile):
    for filetype in SUPPORTED_FILETYPES:

        # Check that file name and extension checking is enforced
        retdata = ReturnedData(data=b'testtext', filetype=filetype)
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


def test_ClientRequest():
    """Test that a ClientRequest gets set up correctly.
    """
    request = ClientRequest('', '', '')
    assert isinstance(request._wps_service,
                      viresclient._wps.wps_vires.ViresWPS10Service
                      )
