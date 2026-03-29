import pytest
from unittest.mock import patch, MagicMock
from dxrpy.datasource.manager import DatasourceAttribute, DatasourceInfo, DatasourceManager


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


def _attr(attribute_type_id=12, value="/data"):
    return DatasourceAttribute(attribute_type_id=attribute_type_id, value=value)


# ---------------------------------------------------------------------------
# DatasourceAttribute
# ---------------------------------------------------------------------------

class TestDatasourceAttribute:
    def test_to_dict(self):
        attr = DatasourceAttribute(attribute_type_id=12, value="/data/scans")
        d = attr.to_dict()
        assert d["datasourceConnectorTypeAttributeId"] == 12
        assert d["value"] == "/data/scans"


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
        result = DatasourceManager().list()
        assert len(result) == 2
        assert all(isinstance(r, DatasourceInfo) for r in result)
        mock_client.get.assert_called_once_with("/datasources")

    def test_paged_envelope(self, mock_client):
        mock_client.get.return_value = {"content": [_ds_payload(3)], "totalElements": 1}
        result = DatasourceManager().list()
        assert len(result) == 1
        assert result[0].id == 3


# ---------------------------------------------------------------------------
# DatasourceManager.get
# ---------------------------------------------------------------------------

class TestDatasourceManagerGet:
    def test_get_by_id(self, mock_client):
        mock_client.get.return_value = _ds_payload(id=99, name="specific")
        result = DatasourceManager().get(99)
        assert result.id == 99
        mock_client.get.assert_called_once_with("/datasources/99")


# ---------------------------------------------------------------------------
# DatasourceManager.find_by_name
# ---------------------------------------------------------------------------

class TestDatasourceManagerFindByName:
    def test_found(self, mock_client):
        mock_client.get.return_value = [_ds_payload(1, "alpha"), _ds_payload(2, "beta")]
        result = DatasourceManager().find_by_name("beta")
        assert result is not None
        assert result.id == 2

    def test_not_found(self, mock_client):
        mock_client.get.return_value = [_ds_payload(1, "alpha")]
        assert DatasourceManager().find_by_name("gamma") is None


# ---------------------------------------------------------------------------
# DatasourceManager.create
# ---------------------------------------------------------------------------

class TestDatasourceManagerCreate:
    def test_create_minimal(self, mock_client):
        mock_client.post.return_value = _ds_payload(id=10, name="new-ds")
        result = DatasourceManager().create(
            name="new-ds",
            connector_type_id=7,
            attributes=[_attr()],
        )
        assert result.id == 10
        payload = mock_client.post.call_args.kwargs["json"]
        assert payload["name"] == "new-ds"
        assert payload["datasourceConnectorTypeId"] == 7
        assert len(payload["datasourceAttributesDTOList"]) == 1
        assert payload["datasourceAttributesDTOList"][0]["datasourceConnectorTypeAttributeId"] == 12
        assert payload["datasourceAttributesDTOList"][0]["value"] == "/data"
        assert "settingsProfileId" not in payload

    def test_create_uses_with_attributes_endpoint(self, mock_client):
        mock_client.post.return_value = _ds_payload(id=10)
        DatasourceManager().create(name="ds", connector_type_id=7, attributes=[_attr()])
        assert mock_client.post.call_args.args[0] == "/datasources/with-attributes"

    def test_create_with_profile(self, mock_client):
        mock_client.post.return_value = _ds_payload(id=11)
        DatasourceManager().create(
            name="ds", connector_type_id=7, attributes=[_attr()], settings_profile_id=50217
        )
        payload = mock_client.post.call_args.kwargs["json"]
        assert payload["settingsProfileId"] == 50217

    def test_create_multiple_attributes(self, mock_client):
        mock_client.post.return_value = _ds_payload(id=12)
        DatasourceManager().create(
            name="ds",
            connector_type_id=7,
            attributes=[_attr(12, "/data"), _attr(13, "tenant-123")],
        )
        payload = mock_client.post.call_args.kwargs["json"]
        assert len(payload["datasourceAttributesDTOList"]) == 2

    def test_create_empty_attributes(self, mock_client):
        mock_client.post.return_value = _ds_payload(id=14)
        DatasourceManager().create(name="ds", connector_type_id=21, attributes=[])
        payload = mock_client.post.call_args.kwargs["json"]
        assert payload["datasourceAttributesDTOList"] == []

    def test_create_with_description(self, mock_client):
        mock_client.post.return_value = _ds_payload(id=13)
        DatasourceManager().create(
            name="ds", connector_type_id=7, attributes=[_attr()], description="test"
        )
        assert mock_client.post.call_args.kwargs["json"]["description"] == "test"


# ---------------------------------------------------------------------------
# DatasourceManager.update
# ---------------------------------------------------------------------------

class TestDatasourceManagerUpdate:
    def test_update_fetches_current_and_merges(self, mock_client):
        current = _ds_payload(id=5, name="old")
        mock_client.get.return_value = current
        mock_client.put.return_value = {**current, "name": "renamed"}

        result = DatasourceManager().update(5, name="renamed")
        assert result.name == "renamed"
        mock_client.get.assert_called_once_with("/datasources/5")
        payload = mock_client.put.call_args.kwargs["json"]
        assert payload["name"] == "renamed"
        assert payload["id"] == 5  # preserved from current

    def test_update_uses_correct_endpoint(self, mock_client):
        mock_client.get.return_value = _ds_payload(id=5)
        mock_client.put.return_value = _ds_payload(id=5)
        DatasourceManager().update(5, name="x")
        assert mock_client.put.call_args.args[0] == "/datasources"

    def test_update_omits_nones(self, mock_client):
        current = _ds_payload(id=5, name="keep")
        mock_client.get.return_value = current
        mock_client.put.return_value = current
        DatasourceManager().update(5)
        payload = mock_client.put.call_args.kwargs["json"]
        assert payload["name"] == "keep"  # preserved from current


# ---------------------------------------------------------------------------
# DatasourceManager.delete
# ---------------------------------------------------------------------------

class TestDatasourceManagerDelete:
    def test_delete_calls_correct_endpoint(self, mock_client):
        mock_client.delete.return_value = None
        DatasourceManager().delete(7)
        mock_client.delete.assert_called_once_with("/datasources/7")


# ---------------------------------------------------------------------------
# DatasourceManager.find_by_connector_type
# ---------------------------------------------------------------------------

class TestDatasourceManagerFindByConnectorType:
    def test_found(self, mock_client):
        mock_client.get.return_value = [
            _ds_payload(1, "alpha"),
            _ds_payload(2, "beta"),
        ]
        result = DatasourceManager().find_by_connector_type(7)
        assert result is not None
        assert result.id == 1  # first match

    def test_not_found(self, mock_client):
        mock_client.get.return_value = [_ds_payload(1, "alpha")]
        assert DatasourceManager().find_by_connector_type(999) is None

    def test_empty_list(self, mock_client):
        mock_client.get.return_value = []
        assert DatasourceManager().find_by_connector_type(7) is None


# ---------------------------------------------------------------------------
# DatasourceManager.find_by_name_prefix
# ---------------------------------------------------------------------------

class TestDatasourceManagerFindByNamePrefix:
    def test_found_multiple(self, mock_client):
        mock_client.get.return_value = [
            _ds_payload(1, "bench__exp1"),
            _ds_payload(2, "bench__exp2"),
            _ds_payload(3, "other-ds"),
        ]
        result = DatasourceManager().find_by_name_prefix("bench__")
        assert len(result) == 2
        assert {r.id for r in result} == {1, 2}

    def test_none_match(self, mock_client):
        mock_client.get.return_value = [_ds_payload(1, "alpha")]
        result = DatasourceManager().find_by_name_prefix("missing-")
        assert result == []

    def test_empty_prefix_matches_all(self, mock_client):
        mock_client.get.return_value = [_ds_payload(1, "a"), _ds_payload(2, "b")]
        result = DatasourceManager().find_by_name_prefix("")
        assert len(result) == 2
