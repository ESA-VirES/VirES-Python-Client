from viresclient._data_handling import ReturnedData
from viresclient import ClientRequest
import viresclient


def test_ReturnedData():
    """Test that supported file types get set up correctly.
    # TODO: Test that file is written / not overwritten correctly.
    """
    retdata = ReturnedData(data=b'', filetype='CSV')
    assert retdata.filetype == 'csv'
    assert retdata.data == b''
    retdata = ReturnedData(data=b'', filetype='CDF')
    assert retdata.filetype == 'cdf'
    assert retdata.data == b''


def test_ClientRequest():
    """Test that a ClientRequest gets set up correctly.
    """
    request = ClientRequest('', '', '')
    assert isinstance(request._wps,
                      viresclient._wps.wps_vires.ViresWPS10Service
                      )
