import pytest

from viresclient._client import ClientRequest
from viresclient import SwarmRequest, AeolusRequest
import viresclient


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
