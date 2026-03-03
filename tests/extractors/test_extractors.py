import pytest
from unittest.mock import patch, MagicMock, call
from dxrpy.extractors.extractors import ExtractorInfo, Extractors, DATA_TYPES


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_client():
    with patch("dxrpy.dxr_client.DXRHttpClient.get_instance") as mock_get_instance:
        client = MagicMock()
        mock_get_instance.return_value = client
        yield client


def _extractor_payload(
    id=1,
    name="Employment Status",
    data_type="BOOLEAN",
    prompt_template="Is the person employed? {{document_text}}",
):
    return {
        "id": id,
        "name": name,
        "description": "",
        "type": "llm",
        "promptTemplate": prompt_template,
        "dataType": data_type,
        "temperature": 0.7,
        "useDocumentContent": False,
        "modelId": None,
    }


# ---------------------------------------------------------------------------
# ExtractorInfo
# ---------------------------------------------------------------------------

class TestExtractorInfo:
    def test_fields_populated(self):
        data = _extractor_payload(id=594, name="My Extractor", data_type="TEXT")
        info = ExtractorInfo(data)
        assert info.id == 594
        assert info.name == "My Extractor"
        assert info.data_type == "TEXT"
        assert info.prompt_template == "Is the person employed? {{document_text}}"
        assert info.temperature == 0.7
        assert info.use_document_content is False
        assert info.model_id is None
        assert info.raw is data

    def test_repr(self):
        info = ExtractorInfo(_extractor_payload(id=1, name="Test", data_type="NUMBER"))
        assert "Test" in repr(info)
        assert "NUMBER" in repr(info)

    def test_missing_optional_fields(self):
        info = ExtractorInfo({"id": 1, "name": "bare"})
        assert info.description is None
        assert info.prompt_template is None
        assert info.data_type is None
        assert info.temperature == 0.7
        assert info.use_document_content is False


# ---------------------------------------------------------------------------
# DATA_TYPES constant
# ---------------------------------------------------------------------------

def test_valid_data_types():
    assert "TEXT" in DATA_TYPES
    assert "NUMBER" in DATA_TYPES
    assert "BOOLEAN" in DATA_TYPES


# ---------------------------------------------------------------------------
# Extractors.list
# ---------------------------------------------------------------------------

class TestExtractorsList:
    def test_returns_list(self, mock_client):
        mock_client.get.return_value = [_extractor_payload(1), _extractor_payload(2)]
        result = Extractors().list()
        assert len(result) == 2
        assert all(isinstance(r, ExtractorInfo) for r in result)
        mock_client.get.assert_called_once_with("/api/metadata-extractors")

    def test_paged_envelope(self, mock_client):
        mock_client.get.return_value = {"content": [_extractor_payload(5)]}
        result = Extractors().list()
        assert len(result) == 1


# ---------------------------------------------------------------------------
# Extractors.get
# ---------------------------------------------------------------------------

class TestExtractorsGet:
    def test_get_by_id(self, mock_client):
        mock_client.get.return_value = _extractor_payload(id=594)
        result = Extractors().get(594)
        assert result.id == 594
        mock_client.get.assert_called_once_with("/api/metadata-extractors/594")


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
    def test_create_boolean(self, mock_client):
        mock_client.post.return_value = _extractor_payload(id=100, data_type="BOOLEAN")
        result = Extractors().create(
            name="Employed?",
            prompt_template="Is employed? {{document_text}}",
            data_type="BOOLEAN",
        )
        assert result.id == 100
        payload = mock_client.post.call_args.kwargs["json"]
        assert payload["name"] == "Employed?"
        assert payload["promptTemplate"] == "Is employed? {{document_text}}"
        assert payload["dataType"] == "BOOLEAN"
        assert payload["type"] == "llm"
        assert payload["description"] == ""
        assert payload["temperature"] == 0.7
        assert payload["useDocumentContent"] is False
        assert "modelId" not in payload

    def test_create_text(self, mock_client):
        mock_client.post.return_value = _extractor_payload(id=101, data_type="TEXT")
        Extractors().create(
            name="Name",
            prompt_template="Extract name. {{document_text}}",
            data_type="TEXT",
        )
        payload = mock_client.post.call_args.kwargs["json"]
        assert payload["dataType"] == "TEXT"

    def test_create_number(self, mock_client):
        mock_client.post.return_value = _extractor_payload(id=102, data_type="NUMBER")
        Extractors().create(
            name="Salary",
            prompt_template="Extract salary. {{document_text}}",
            data_type="NUMBER",
        )
        payload = mock_client.post.call_args.kwargs["json"]
        assert payload["dataType"] == "NUMBER"

    def test_create_with_temperature(self, mock_client):
        mock_client.post.return_value = _extractor_payload(id=103)
        Extractors().create(
            name="X",
            prompt_template="{{document_text}}",
            data_type="TEXT",
            temperature=0.2,
        )
        assert mock_client.post.call_args.kwargs["json"]["temperature"] == 0.2

    def test_create_with_model_id(self, mock_client):
        mock_client.post.return_value = _extractor_payload(id=104)
        Extractors().create(
            name="X",
            prompt_template="{{document_text}}",
            data_type="TEXT",
            model_id="some-uuid",
        )
        assert mock_client.post.call_args.kwargs["json"]["modelId"] == "some-uuid"

    def test_invalid_data_type_raises(self, mock_client):
        with pytest.raises(ValueError, match="Invalid data_type"):
            Extractors().create(
                name="X",
                prompt_template="{{document_text}}",
                data_type="PERSON",  # entity type, not a DataType
            )

    def test_uses_correct_endpoint(self, mock_client):
        mock_client.post.return_value = _extractor_payload(id=105)
        Extractors().create(name="X", prompt_template="{{document_text}}", data_type="TEXT")
        assert mock_client.post.call_args.args[0] == "/api/metadata-extractors"


# ---------------------------------------------------------------------------
# Extractors.update
# ---------------------------------------------------------------------------

class TestExtractorsUpdate:
    def test_update_fetches_current_and_merges(self, mock_client):
        current = _extractor_payload(id=5, name="Old", data_type="TEXT")
        mock_client.get.return_value = current
        mock_client.put.return_value = {**current, "name": "New"}

        result = Extractors().update(5, name="New")
        assert result.name == "New"

        # Should have fetched current state first
        mock_client.get.assert_called_once_with("/api/metadata-extractors/5")
        # PUT payload includes id and merged fields
        payload = mock_client.put.call_args.kwargs["json"]
        assert payload["id"] == 5
        assert payload["name"] == "New"
        assert payload["dataType"] == "TEXT"  # preserved from current

    def test_update_prompt_template(self, mock_client):
        current = _extractor_payload(id=7)
        mock_client.get.return_value = current
        mock_client.put.return_value = {**current, "promptTemplate": "New prompt"}

        Extractors().update(7, prompt_template="New prompt")
        payload = mock_client.put.call_args.kwargs["json"]
        assert payload["promptTemplate"] == "New prompt"

    def test_update_uses_correct_endpoint(self, mock_client):
        mock_client.get.return_value = _extractor_payload(id=7)
        mock_client.put.return_value = _extractor_payload(id=7)
        Extractors().update(7, name="Updated")
        assert mock_client.put.call_args.args[0] == "/api/metadata-extractors/7"

    def test_invalid_data_type_raises(self, mock_client):
        mock_client.get.return_value = _extractor_payload(id=1)
        with pytest.raises(ValueError, match="Invalid data_type"):
            Extractors().update(1, data_type="EMAIL_ADDRESS")


# ---------------------------------------------------------------------------
# Extractors.delete
# ---------------------------------------------------------------------------

class TestExtractorsDelete:
    def test_delete(self, mock_client):
        mock_client.delete.return_value = None
        Extractors().delete(99)
        mock_client.delete.assert_called_once_with("/api/metadata-extractors/99")
