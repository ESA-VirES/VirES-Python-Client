import pytest
import os
import pandas as pd

from viresclient._data_handling import ReturnedData
from viresclient._client import ClientRequest
from viresclient import SwarmRequest, AeolusRequest
import viresclient

SUPPORTED_FILETYPES = ('csv', 'cdf', 'nc')


def test_ReturnedData_setup():
    """Test the ReturnedData functionality

    Enforcement of filetype as csv/cdf/nc
    Writing files and dealing correctly with overwrite or not
    TODO: creation of dataframe
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


def test_ClientRequest():
    """Test that a ClientRequest gets set up correctly.
    """
    request = ClientRequest('', '', '')
    assert isinstance(request._wps_service,
                      viresclient._wps.wps_vires.ViresWPS10Service
                      )
    request = SwarmRequest('', '', '')
    assert isinstance(request._wps_service,
                      viresclient._wps.wps_vires.ViresWPS10Service
                      )
    request = AeolusRequest('', '', '')
    assert isinstance(request._wps_service,
                      viresclient._wps.wps_vires.ViresWPS10Service
                      )
