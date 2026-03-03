import pytest
from unittest.mock import patch, MagicMock
from dxrpy.smart_labels.smart_labels import SmartLabelInfo, SmartLabelRule, SmartLabels
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


def _label_payload(id=1, name="Has-SSN", type_="SMART"):
    return {
        "id": id,
        "name": name,
        "hexColor": "E74C3C",
        "type": type_,
        "savedQueryDtoList": [],
    }


def _query_item(**kwargs):
    defaults = dict(
        parameter="annotators",
        value="annotation.16",
        type="text",
        match_strategy="exists",
        operator="AND",
        group_id=0,
        group_order=0,
    )
    return JsonSearchQueryItem(**{**defaults, **kwargs})


# ---------------------------------------------------------------------------
# SmartLabelRule
# ---------------------------------------------------------------------------

class TestSmartLabelRule:
    def test_to_dict_with_items(self):
        rule = SmartLabelRule(
            datasource_ids=[50148],
            query_items=[_query_item()],
            status="RUNNING",
        )
        d = rule.to_dict()
        assert d["datasourceIds"] == [50148]
        assert d["status"] == "RUNNING"
        assert len(d["query"]["query_items"]) == 1
        qi = d["query"]["query_items"][0]
        assert qi["parameter"] == "annotators"
        assert qi["match_strategy"] == "exists"

    def test_to_dict_no_query_items(self):
        rule = SmartLabelRule(datasource_ids=[1])
        d = rule.to_dict()
        assert d["query"]["query_items"] == []

    def test_default_status_is_running(self):
        rule = SmartLabelRule(datasource_ids=[1])
        assert rule.status == "RUNNING"


# ---------------------------------------------------------------------------
# SmartLabelInfo
# ---------------------------------------------------------------------------

class TestSmartLabelInfo:
    def test_fields_populated(self):
        data = _label_payload(id=10, name="Sensitive", type_="SMART")
        info = SmartLabelInfo(data)
        assert info.id == 10
        assert info.name == "Sensitive"
        assert info.hex_color == "E74C3C"
        assert info.type == "SMART"
        assert info.raw is data

    def test_standard_type(self):
        info = SmartLabelInfo(_label_payload(type_="STANDARD"))
        assert info.type == "STANDARD"

    def test_repr(self):
        info = SmartLabelInfo(_label_payload(id=5, name="PII"))
        assert "PII" in repr(info)
        assert "SMART" in repr(info)


# ---------------------------------------------------------------------------
# SmartLabels.list / get / find_by_name
# ---------------------------------------------------------------------------

class TestSmartLabelsRead:
    def test_list(self, mock_client):
        mock_client.get.return_value = [_label_payload(1), _label_payload(2)]
        result = SmartLabels().list()
        assert len(result) == 2
        assert all(isinstance(r, SmartLabelInfo) for r in result)
        mock_client.get.assert_called_once_with("/api/tags")

    def test_list_paged_envelope(self, mock_client):
        mock_client.get.return_value = {"content": [_label_payload(3)]}
        result = SmartLabels().list()
        assert len(result) == 1

    def test_get(self, mock_client):
        mock_client.get.return_value = _label_payload(id=42, name="Confidential")
        result = SmartLabels().get(42)
        assert result.id == 42
        mock_client.get.assert_called_once_with("/api/tags/42")

    def test_find_by_name_found(self, mock_client):
        mock_client.get.return_value = [_label_payload(1, "Alpha"), _label_payload(2, "Beta")]
        result = SmartLabels().find_by_name("Beta")
        assert result is not None
        assert result.id == 2

    def test_find_by_name_not_found(self, mock_client):
        mock_client.get.return_value = [_label_payload(1, "Alpha")]
        assert SmartLabels().find_by_name("Gamma") is None


# ---------------------------------------------------------------------------
# SmartLabels.create
# ---------------------------------------------------------------------------

class TestSmartLabelsCreate:
    def test_create_standard_tag(self, mock_client):
        mock_client.post.return_value = _label_payload(id=20, name="Reviewed", type_="STANDARD")
        result = SmartLabels().create(name="Reviewed", hex_color="3498DB")
        assert result.id == 20
        payload = mock_client.post.call_args.kwargs["json"]
        assert payload["name"] == "Reviewed"
        assert payload["hexColor"] == "3498DB"
        assert payload["type"] == "STANDARD"
        assert "savedQueryDtoList" not in payload

    def test_create_smart_label_with_rules(self, mock_client):
        mock_client.post.return_value = _label_payload(id=21, type_="SMART")
        rules = [SmartLabelRule(datasource_ids=[50148], query_items=[_query_item()])]
        SmartLabels().create(name="Has-SSN", hex_color="E74C3C", rules=rules)
        payload = mock_client.post.call_args.kwargs["json"]
        assert payload["type"] == "SMART"
        assert len(payload["savedQueryDtoList"]) == 1
        rule_dict = payload["savedQueryDtoList"][0]
        assert rule_dict["datasourceIds"] == [50148]
        assert rule_dict["status"] == "RUNNING"
        assert len(rule_dict["query"]["query_items"]) == 1

    def test_create_uses_hex_color_field(self, mock_client):
        mock_client.post.return_value = _label_payload(id=22)
        SmartLabels().create(name="X", hex_color="123456")
        payload = mock_client.post.call_args.kwargs["json"]
        assert "hexColor" in payload
        assert "color" not in payload

    def test_create_multiple_rules(self, mock_client):
        mock_client.post.return_value = _label_payload(id=23)
        rules = [
            SmartLabelRule(datasource_ids=[1], query_items=[_query_item()]),
            SmartLabelRule(datasource_ids=[2], query_items=[_query_item(value="annotation.99")]),
        ]
        SmartLabels().create(name="Multi", hex_color="FFFFFF", rules=rules)
        payload = mock_client.post.call_args.kwargs["json"]
        assert len(payload["savedQueryDtoList"]) == 2

    def test_create_with_description(self, mock_client):
        mock_client.post.return_value = _label_payload(id=24)
        SmartLabels().create(name="X", hex_color="000000", description="A label")
        assert mock_client.post.call_args.kwargs["json"]["description"] == "A label"


# ---------------------------------------------------------------------------
# SmartLabels.update
# ---------------------------------------------------------------------------

class TestSmartLabelsUpdate:
    def test_update_fetches_current_and_merges(self, mock_client):
        current = _label_payload(id=5, name="Old")
        mock_client.get.return_value = current
        mock_client.put.return_value = {**current, "name": "New"}

        result = SmartLabels().update(5, name="New")
        assert result.name == "New"
        mock_client.get.assert_called_once_with("/api/tags/5")
        payload = mock_client.put.call_args.kwargs["json"]
        assert payload["name"] == "New"
        assert payload["id"] == 5

    def test_update_uses_put_api_tags(self, mock_client):
        mock_client.get.return_value = _label_payload(id=5)
        mock_client.put.return_value = _label_payload(id=5)
        SmartLabels().update(5, name="X")
        # PUT /api/tags (no ID in path)
        assert mock_client.put.call_args.args[0] == "/api/tags"

    def test_update_rules(self, mock_client):
        current = _label_payload(id=5)
        mock_client.get.return_value = current
        mock_client.put.return_value = current
        new_rules = [SmartLabelRule(datasource_ids=[99], query_items=[_query_item()])]
        SmartLabels().update(5, rules=new_rules)
        payload = mock_client.put.call_args.kwargs["json"]
        assert payload["type"] == "SMART"
        assert len(payload["savedQueryDtoList"]) == 1

    def test_update_hex_color(self, mock_client):
        mock_client.get.return_value = _label_payload(id=5)
        mock_client.put.return_value = _label_payload(id=5)
        SmartLabels().update(5, hex_color="ABCDEF")
        payload = mock_client.put.call_args.kwargs["json"]
        assert payload["hexColor"] == "ABCDEF"


# ---------------------------------------------------------------------------
# SmartLabels.delete
# ---------------------------------------------------------------------------

class TestSmartLabelsDelete:
    def test_delete(self, mock_client):
        mock_client.delete.return_value = None
        SmartLabels().delete(9)
        mock_client.delete.assert_called_once_with("/api/tags/9")
