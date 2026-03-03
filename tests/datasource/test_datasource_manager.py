import pytest
from unittest.mock import patch, MagicMock
from dxrpy.datasource.manager import DatasourceInfo, DatasourceManager


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_client():
    with patch("dxrpy.dxr_client.DXRHttpClient.get_instance") as mock_get_instance:
        client = MagicMock()
        mock_get_instance.return_value = client
        yield client


def _ds_payload(id=1, name="test-ds", status="ACTIVE"):
    return {
        "id": id,
        "name": name,
        "status": status,
        "datasourceConnectorTypeId": 7,
        "datasourceConnectorTypeName": "OnDemand",
        "settingsProfile": {"id": 50217},
    }


# ---------------------------------------------------------------------------
# DatasourceInfo
# ---------------------------------------------------------------------------

class TestDatasourceInfo:
    def test_fields_populated(self):
        data = _ds_payload(id=42, name="my-ds", status="IDLE")
        info = DatasourceInfo(data)
        assert info.id == 42
        assert info.name == "my-ds"
        assert info.status == "IDLE"
        assert info.connector_type_id == 7
        assert info.settings_profile_id == 50217
        assert info.raw is data

    def test_repr(self):
        info = DatasourceInfo(_ds_payload(id=1, name="foo"))
        assert "foo" in repr(info)

    def test_missing_settings_profile(self):
        data = {"id": 1, "name": "bare"}
        info = DatasourceInfo(data)
        assert info.settings_profile_id is None


# ---------------------------------------------------------------------------
# DatasourceManager.list
# ---------------------------------------------------------------------------

class TestDatasourceManagerList:
    def test_returns_list(self, mock_client):
        mock_client.get.return_value = [_ds_payload(1), _ds_payload(2)]
        mgr = DatasourceManager()
        result = mgr.list()
        assert len(result) == 2
        assert all(isinstance(r, DatasourceInfo) for r in result)
        mock_client.get.assert_called_once_with("/api/datasources")

    def test_paged_envelope(self, mock_client):
        mock_client.get.return_value = {"content": [_ds_payload(3)], "totalElements": 1}
        mgr = DatasourceManager()
        result = mgr.list()
        assert len(result) == 1
        assert result[0].id == 3


# ---------------------------------------------------------------------------
# DatasourceManager.get
# ---------------------------------------------------------------------------

class TestDatasourceManagerGet:
    def test_get_by_id(self, mock_client):
        mock_client.get.return_value = _ds_payload(id=99, name="specific")
        mgr = DatasourceManager()
        result = mgr.get(99)
        assert result.id == 99
        assert result.name == "specific"
        mock_client.get.assert_called_once_with("/api/datasources/99")


# ---------------------------------------------------------------------------
# DatasourceManager.find_by_name
# ---------------------------------------------------------------------------

class TestDatasourceManagerFindByName:
    def test_found(self, mock_client):
        mock_client.get.return_value = [
            _ds_payload(1, "alpha"),
            _ds_payload(2, "beta"),
        ]
        mgr = DatasourceManager()
        result = mgr.find_by_name("beta")
        assert result is not None
        assert result.id == 2

    def test_not_found(self, mock_client):
        mock_client.get.return_value = [_ds_payload(1, "alpha")]
        mgr = DatasourceManager()
        assert mgr.find_by_name("gamma") is None


# ---------------------------------------------------------------------------
# DatasourceManager.create
# ---------------------------------------------------------------------------

class TestDatasourceManagerCreate:
    def test_create_minimal(self, mock_client):
        mock_client.post.return_value = _ds_payload(id=10, name="new-ds")
        mgr = DatasourceManager()
        result = mgr.create(name="new-ds", connector_type_id=7)
        assert result.id == 10
        called_payload = mock_client.post.call_args.kwargs["json"]
        assert called_payload["name"] == "new-ds"
        assert called_payload["datasourceConnectorTypeId"] == 7
        assert "settingsProfileId" not in called_payload

    def test_create_with_profile(self, mock_client):
        mock_client.post.return_value = _ds_payload(id=11)
        mgr = DatasourceManager()
        mgr.create(name="ds-with-profile", connector_type_id=7, settings_profile_id=50217)
        payload = mock_client.post.call_args.kwargs["json"]
        assert payload["settingsProfileId"] == 50217

    def test_create_with_description(self, mock_client):
        mock_client.post.return_value = _ds_payload(id=12)
        mgr = DatasourceManager()
        mgr.create(name="ds", connector_type_id=7, description="for benchmarks")
        payload = mock_client.post.call_args.kwargs["json"]
        assert payload["description"] == "for benchmarks"

    def test_create_extra_fields(self, mock_client):
        mock_client.post.return_value = _ds_payload(id=13)
        mgr = DatasourceManager()
        mgr.create(name="ds", connector_type_id=7, monitorable=False)
        payload = mock_client.post.call_args.kwargs["json"]
        assert payload["monitorable"] is False


# ---------------------------------------------------------------------------
# DatasourceManager.update
# ---------------------------------------------------------------------------

class TestDatasourceManagerUpdate:
    def test_update_name(self, mock_client):
        mock_client.put.return_value = _ds_payload(id=5, name="renamed")
        mgr = DatasourceManager()
        result = mgr.update(5, name="renamed")
        assert result.name == "renamed"
        payload = mock_client.put.call_args.kwargs["json"]
        assert payload["name"] == "renamed"
        mock_client.put.assert_called_once_with("/api/datasources/5", json=payload)

    def test_update_omits_nones(self, mock_client):
        mock_client.put.return_value = _ds_payload(id=5)
        mgr = DatasourceManager()
        mgr.update(5)
        payload = mock_client.put.call_args.kwargs["json"]
        assert "name" not in payload
        assert "settingsProfileId" not in payload


# ---------------------------------------------------------------------------
# DatasourceManager.delete
# ---------------------------------------------------------------------------

class TestDatasourceManagerDelete:
    def test_delete_calls_correct_endpoint(self, mock_client):
        mock_client.delete.return_value = None
        mgr = DatasourceManager()
        mgr.delete(7)
        mock_client.delete.assert_called_once_with("/api/datasources/7")
