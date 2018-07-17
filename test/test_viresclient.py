import pytest
import os
import pandas as pd

from viresclient._data_handling import ReturnedData
from viresclient import ClientRequest
import viresclient


def test_ReturnedData():
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

    # Check that file name and extension checking is enforced
    retdata = ReturnedData(data=b'testtext', filetype='csv')
    with pytest.raises(TypeError):
        retdata.to_file(1)
    with pytest.raises(TypeError):
        retdata.to_file('testfile.xyz')
    retdata.to_file('testfile.csv')
    # Check that not overwriting and overwriting work right
    with pytest.raises(FileExistsError):
        retdata.to_file('testfile.csv', overwrite=False)
    retdata.to_file('testfile.csv', overwrite=True)
    os.remove('testfile.csv')
    # # Check that dataframe is created
    # df = retdata.as_dataframe()
    # assert isinstance(df, pd.DataFrame)

    # Repeat the above for CDF
    retdata = ReturnedData(data=b'testtext', filetype='cdf')
    with pytest.raises(TypeError):
        retdata.to_file(1)
    with pytest.raises(TypeError):
        retdata.to_file('testfile.xyz')
    retdata.to_file('testfile.cdf')
    # Check that not overwriting and overwriting work right
    with pytest.raises(FileExistsError):
        retdata.to_file('testfile.cdf', overwrite=False)
    retdata.to_file('testfile.cdf', overwrite=True)
    os.remove('testfile.cdf')
    # # Check that dataframe is created
    # df = retdata.as_dataframe()
    # assert isinstance(df, pd.DataFrame)


def test_ClientRequest():
    """Test that a ClientRequest gets set up correctly.
    """
    request = ClientRequest('', '', '')
    assert isinstance(request._wps,
                      viresclient._wps.wps_vires.ViresWPS10Service
                      )
