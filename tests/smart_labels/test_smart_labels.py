import pytest
from unittest.mock import patch, MagicMock
from dxrpy.smart_labels.smart_labels import SmartLabelInfo, SmartLabels
from dxrpy.index.json_search_query import JsonSearchQueryItem


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_client():
    with patch("dxrpy.dxr_client.DXRHttpClient.get_instance") as mock_get_instance:
        client = MagicMock()
        mock_get_instance.return_value = client
        yield client


def _label_payload(id=1, name="Has-SSN", datasource_ids=None):
    return {
        "id": id,
        "name": name,
        "color": "#FF5733",
        "datasourceIds": datasource_ids or [50148],
    }


# ---------------------------------------------------------------------------
# SmartLabelInfo
# ---------------------------------------------------------------------------

class TestSmartLabelInfo:
    def test_fields_populated(self):
        data = _label_payload(id=10, name="Sensitive", datasource_ids=[1, 2])
        info = SmartLabelInfo(data)
        assert info.id == 10
        assert info.name == "Sensitive"
        assert info.color == "#FF5733"
        assert info.datasource_ids == [1, 2]
        assert info.raw is data

    def test_repr(self):
        info = SmartLabelInfo(_label_payload(id=5, name="PII"))
        assert "PII" in repr(info)

    def test_missing_datasource_ids(self):
        info = SmartLabelInfo({"id": 1, "name": "bare"})
        assert info.datasource_ids == []


# ---------------------------------------------------------------------------
# SmartLabels.list
# ---------------------------------------------------------------------------

class TestSmartLabelsList:
    def test_returns_list(self, mock_client):
        mock_client.get.return_value = [_label_payload(1), _label_payload(2)]
        result = SmartLabels().list()
        assert len(result) == 2
        assert all(isinstance(r, SmartLabelInfo) for r in result)
        mock_client.get.assert_called_once_with("/api/tags")

    def test_paged_envelope(self, mock_client):
        mock_client.get.return_value = {"content": [_label_payload(3)]}
        result = SmartLabels().list()
        assert len(result) == 1


# ---------------------------------------------------------------------------
# SmartLabels.get
# ---------------------------------------------------------------------------

class TestSmartLabelsGet:
    def test_get_by_id(self, mock_client):
        mock_client.get.return_value = _label_payload(id=42, name="Confidential")
        result = SmartLabels().get(42)
        assert result.id == 42
        mock_client.get.assert_called_once_with("/api/tags/42")


# ---------------------------------------------------------------------------
# SmartLabels.find_by_name
# ---------------------------------------------------------------------------

class TestSmartLabelsFindByName:
    def test_found(self, mock_client):
        mock_client.get.return_value = [
            _label_payload(1, "Alpha"),
            _label_payload(2, "Beta"),
        ]
        result = SmartLabels().find_by_name("Beta")
        assert result is not None
        assert result.id == 2

    def test_not_found(self, mock_client):
        mock_client.get.return_value = [_label_payload(1, "Alpha")]
        assert SmartLabels().find_by_name("Gamma") is None


# ---------------------------------------------------------------------------
# SmartLabels.create
# ---------------------------------------------------------------------------

class TestSmartLabelsCreate:
    def test_create_minimal(self, mock_client):
        mock_client.post.return_value = _label_payload(id=20, name="New")
        result = SmartLabels().create(name="New", datasource_ids=[1])
        assert result.id == 20
        payload = mock_client.post.call_args.kwargs["json"]
        assert payload["name"] == "New"
        assert payload["datasourceIds"] == [1]
        assert "savedQuery" not in payload

    def test_create_with_query_items(self, mock_client):
        mock_client.post.return_value = _label_payload(id=21)
        items = [
            JsonSearchQueryItem(
                parameter="annotators",
                value="annotation.16",
                type="text",
                match_strategy="exists",
            )
        ]
        SmartLabels().create(name="Has-SSN", datasource_ids=[50148], query_items=items)
        payload = mock_client.post.call_args.kwargs["json"]
        assert "savedQuery" in payload
        assert len(payload["savedQuery"]["query_items"]) == 1
        qi = payload["savedQuery"]["query_items"][0]
        assert qi["parameter"] == "annotators"
        assert qi["match_strategy"] == "exists"

    def test_create_with_color(self, mock_client):
        mock_client.post.return_value = _label_payload(id=22)
        SmartLabels().create(name="X", datasource_ids=[1], color="#123456")
        payload = mock_client.post.call_args.kwargs["json"]
        assert payload["color"] == "#123456"


# ---------------------------------------------------------------------------
# SmartLabels.update
# ---------------------------------------------------------------------------

class TestSmartLabelsUpdate:
    def test_update_name(self, mock_client):
        mock_client.put.return_value = _label_payload(id=5, name="Renamed")
        result = SmartLabels().update(5, name="Renamed")
        assert result.name == "Renamed"
        mock_client.put.assert_called_once()
        payload = mock_client.put.call_args.kwargs["json"]
        assert payload["name"] == "Renamed"
        assert "color" not in payload

    def test_update_query_items(self, mock_client):
        mock_client.put.return_value = _label_payload(id=5)
        items = [JsonSearchQueryItem(parameter="p", value="v", type="text")]
        SmartLabels().update(5, query_items=items)
        payload = mock_client.put.call_args.kwargs["json"]
        assert "savedQuery" in payload


# ---------------------------------------------------------------------------
# SmartLabels.delete
# ---------------------------------------------------------------------------

class TestSmartLabelsDelete:
    def test_delete(self, mock_client):
        mock_client.delete.return_value = None
        SmartLabels().delete(9)
        mock_client.delete.assert_called_once_with("/api/tags/9")
