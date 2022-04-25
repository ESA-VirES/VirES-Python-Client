import viresclient
from viresclient import AeolusRequest, SwarmRequest
from viresclient._client import ClientRequest


def test_ClientRequest():
    """Test that a ClientRequest gets set up correctly."""
    request = ClientRequest("dummy_url")
    assert isinstance(
        request._wps_service, viresclient._wps.wps_vires.ViresWPS10Service
    )
    request = SwarmRequest("dummy_url")
    assert isinstance(
        request._wps_service, viresclient._wps.wps_vires.ViresWPS10Service
    )
    request = AeolusRequest("dummy_url")
    assert isinstance(
        request._wps_service, viresclient._wps.wps_vires.ViresWPS10Service
    )
