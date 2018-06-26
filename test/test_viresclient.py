import viresclient

def test_ReturnedData():
    """Test that supported file types get set up correctly.
    # TODO: Test that file is written / not overwritten correctly.
    """
    retdata = viresclient.viresclient.ReturnedData(data=b'',filetype='CSV')
    assert retdata.filetype == 'csv'
    assert retdata.data == b''
    retdata = viresclient.viresclient.ReturnedData(data=b'',filetype='CDF')
    assert retdata.filetype == 'cdf'
    assert retdata.data == b''

def test_ClientRequest():
    """Test that a ClientRequest gets set up correctly.
    """
    request = viresclient.ClientRequest('','','')
    assert isinstance(request._wps, viresclient.wps.wps_vires.ViresWPS10Service)
