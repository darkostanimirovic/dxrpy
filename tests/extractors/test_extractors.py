import pytest
from unittest.mock import patch, MagicMock
from dxrpy.extractors.extractors import ExtractorInfo, Extractors


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_client():
    with patch("dxrpy.dxr_client.DXRHttpClient.get_instance") as mock_get_instance:
        client = MagicMock()
        mock_get_instance.return_value = client
        yield client


def _extractor_payload(id=1, name="PII Extractor", prompt="Extract PII..."):
    return {
        "id": id,
        "name": name,
        "description": "Extracts PII fields",
        "prompt": prompt,
        "dataTypes": ["PERSON", "EMAIL_ADDRESS"],
    }


# ---------------------------------------------------------------------------
# ExtractorInfo
# ---------------------------------------------------------------------------

class TestExtractorInfo:
    def test_fields_populated(self):
        data = _extractor_payload(id=594, name="My Extractor", prompt="Extract all...")
        info = ExtractorInfo(data)
        assert info.id == 594
        assert info.name == "My Extractor"
        assert info.prompt == "Extract all..."
        assert info.data_types == ["PERSON", "EMAIL_ADDRESS"]
        assert info.raw is data

    def test_repr(self):
        info = ExtractorInfo(_extractor_payload(id=1, name="Test"))
        assert "Test" in repr(info)

    def test_missing_optional_fields(self):
        info = ExtractorInfo({"id": 1, "name": "bare"})
        assert info.description is None
        assert info.prompt is None
        assert info.data_types == []


# ---------------------------------------------------------------------------
# Extractors.list
# ---------------------------------------------------------------------------

class TestExtractorsList:
    def test_returns_list(self, mock_client):
        mock_client.get.return_value = [_extractor_payload(1), _extractor_payload(2)]
        result = Extractors().list()
        assert len(result) == 2
        assert all(isinstance(r, ExtractorInfo) for r in result)
        mock_client.get.assert_called_once_with("/api/extractors")

    def test_paged_envelope(self, mock_client):
        mock_client.get.return_value = {"content": [_extractor_payload(5)]}
        result = Extractors().list()
        assert len(result) == 1


# ---------------------------------------------------------------------------
# Extractors.get
# ---------------------------------------------------------------------------

class TestExtractorsGet:
    def test_get_by_id(self, mock_client):
        mock_client.get.return_value = _extractor_payload(id=594, name="Specific")
        result = Extractors().get(594)
        assert result.id == 594
        mock_client.get.assert_called_once_with("/api/extractors/594")


# ---------------------------------------------------------------------------
# Extractors.find_by_name
# ---------------------------------------------------------------------------

class TestExtractorsFindByName:
    def test_found(self, mock_client):
        mock_client.get.return_value = [
            _extractor_payload(1, "Alpha"),
            _extractor_payload(2, "Beta"),
        ]
        result = Extractors().find_by_name("Beta")
        assert result is not None
        assert result.id == 2

    def test_not_found(self, mock_client):
        mock_client.get.return_value = [_extractor_payload(1, "Alpha")]
        assert Extractors().find_by_name("Gamma") is None


# ---------------------------------------------------------------------------
# Extractors.create
# ---------------------------------------------------------------------------

class TestExtractorsCreate:
    def test_create_minimal(self, mock_client):
        mock_client.post.return_value = _extractor_payload(id=100, name="New")
        result = Extractors().create(name="New", prompt="Extract...")
        assert result.id == 100
        payload = mock_client.post.call_args.kwargs["json"]
        assert payload["name"] == "New"
        assert payload["prompt"] == "Extract..."
        assert "dataTypes" not in payload

    def test_create_with_data_types(self, mock_client):
        mock_client.post.return_value = _extractor_payload(id=101)
        Extractors().create(
            name="PII",
            prompt="...",
            data_types=["PERSON", "EMAIL_ADDRESS"],
        )
        payload = mock_client.post.call_args.kwargs["json"]
        assert payload["dataTypes"] == ["PERSON", "EMAIL_ADDRESS"]

    def test_create_with_description(self, mock_client):
        mock_client.post.return_value = _extractor_payload(id=102)
        Extractors().create(name="X", prompt="...", description="Desc")
        payload = mock_client.post.call_args.kwargs["json"]
        assert payload["description"] == "Desc"

    def test_create_extra_fields(self, mock_client):
        mock_client.post.return_value = _extractor_payload(id=103)
        Extractors().create(name="X", prompt="...", enabled=True)
        payload = mock_client.post.call_args.kwargs["json"]
        assert payload["enabled"] is True


# ---------------------------------------------------------------------------
# Extractors.update
# ---------------------------------------------------------------------------

class TestExtractorsUpdate:
    def test_update_prompt(self, mock_client):
        mock_client.put.return_value = _extractor_payload(id=5, prompt="New prompt")
        result = Extractors().update(5, prompt="New prompt")
        assert result.prompt == "New prompt"
        payload = mock_client.put.call_args.kwargs["json"]
        assert payload["prompt"] == "New prompt"
        assert "name" not in payload

    def test_update_endpoint(self, mock_client):
        mock_client.put.return_value = _extractor_payload(id=7)
        Extractors().update(7, name="Updated")
        mock_client.put.assert_called_once_with("/api/extractors/7", json={"name": "Updated"})


# ---------------------------------------------------------------------------
# Extractors.delete
# ---------------------------------------------------------------------------

class TestExtractorsDelete:
    def test_delete(self, mock_client):
        mock_client.delete.return_value = None
        Extractors().delete(99)
        mock_client.delete.assert_called_once_with("/api/extractors/99")
