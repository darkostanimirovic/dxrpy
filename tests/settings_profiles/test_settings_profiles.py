import json
import pytest
from unittest.mock import patch, MagicMock
from dxrpy.settings_profiles.settings_profiles import (
    SettingsProfileInfo,
    SettingsProfiles,
    WorkflowStep,
    _FIELD_EXTRACTION_ENABLED,
    _FIELD_EXTRACTION_WORKFLOW,
)
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


def _profile_payload(id=50217, name="Default Profile"):
    return {"id": id, "name": name, "description": "Test profile", "type": "STANDARD"}


# ---------------------------------------------------------------------------
# WorkflowStep
# ---------------------------------------------------------------------------

class TestWorkflowStep:
    def test_to_dict_no_condition(self):
        step = WorkflowStep(extractor_id=594)
        d = step.to_dict()
        assert d["type"] == "extractor"
        assert d["extractorId"] == 594
        assert "condition" not in d

    def test_to_dict_with_condition(self):
        items = [
            JsonSearchQueryItem(
                parameter="annotators",
                value="annotation.16",
                type="text",
                match_strategy="exists",
                operator="AND",
                group_id=0,
                group_order=0,
            )
        ]
        step = WorkflowStep(extractor_id=594, condition=items)
        d = step.to_dict()
        assert "condition" in d
        qi = d["condition"]["query_items"][0]
        assert qi["parameter"] == "annotators"
        assert qi["value"] == "annotation.16"
        assert qi["match_strategy"] == "exists"

    def test_empty_condition_list_omitted(self):
        step = WorkflowStep(extractor_id=1, condition=[])
        d = step.to_dict()
        assert "condition" not in d


# ---------------------------------------------------------------------------
# SettingsProfileInfo
# ---------------------------------------------------------------------------

class TestSettingsProfileInfo:
    def test_fields_populated(self):
        data = _profile_payload(id=99, name="Production")
        info = SettingsProfileInfo(data)
        assert info.id == 99
        assert info.name == "Production"
        assert info.type == "STANDARD"
        assert info.raw is data

    def test_repr(self):
        info = SettingsProfileInfo(_profile_payload(id=1, name="My Profile"))
        assert "My Profile" in repr(info)


# ---------------------------------------------------------------------------
# SettingsProfiles.list / get / find_by_name
# ---------------------------------------------------------------------------

class TestSettingsProfilesRead:
    def test_list(self, mock_client):
        mock_client.get.return_value = [_profile_payload(1), _profile_payload(2)]
        result = SettingsProfiles().list()
        assert len(result) == 2
        mock_client.get.assert_called_once_with("/api/settings-profiles")

    def test_list_paged_envelope(self, mock_client):
        mock_client.get.return_value = {"content": [_profile_payload(3)]}
        result = SettingsProfiles().list()
        assert len(result) == 1

    def test_get(self, mock_client):
        mock_client.get.return_value = _profile_payload(id=50217)
        result = SettingsProfiles().get(50217)
        assert result.id == 50217
        mock_client.get.assert_called_once_with("/api/settings-profiles/50217")

    def test_find_by_name_found(self, mock_client):
        mock_client.get.return_value = [
            _profile_payload(1, "Alpha"),
            _profile_payload(2, "Beta"),
        ]
        result = SettingsProfiles().find_by_name("Beta")
        assert result is not None
        assert result.id == 2

    def test_find_by_name_not_found(self, mock_client):
        mock_client.get.return_value = [_profile_payload(1, "Alpha")]
        assert SettingsProfiles().find_by_name("Gamma") is None


# ---------------------------------------------------------------------------
# SettingsProfiles.set_extraction_workflow
# ---------------------------------------------------------------------------

class TestSetExtractionWorkflow:
    def test_basic_unconditional_extractor(self, mock_client):
        mock_client.patch.return_value = None
        SettingsProfiles().set_extraction_workflow(
            profile_id=50217,
            enabled=True,
            steps=[WorkflowStep(extractor_id=594)],
        )
        mock_client.patch.assert_called_once()
        payload = mock_client.patch.call_args.kwargs["json"]
        assert payload["profile_id"] == 50217

        configs = {c["settings_config_field_id"]: c["config_value"] for c in payload["settings_profile_configurations"]}
        assert configs[_FIELD_EXTRACTION_ENABLED] == "true"
        workflow = json.loads(configs[_FIELD_EXTRACTION_WORKFLOW])
        assert len(workflow["statements"]) == 1
        stmt = workflow["statements"][0]
        assert stmt["type"] == "extractor"
        assert stmt["extractorId"] == 594
        assert "condition" not in stmt

    def test_workflow_with_condition(self, mock_client):
        mock_client.patch.return_value = None
        items = [
            JsonSearchQueryItem(
                parameter="annotators",
                value="annotation.16",
                type="text",
                match_strategy="exists",
                operator="AND",
                group_id=0,
                group_order=0,
            )
        ]
        SettingsProfiles().set_extraction_workflow(
            profile_id=50217,
            enabled=True,
            steps=[WorkflowStep(extractor_id=594, condition=items)],
        )
        payload = mock_client.patch.call_args.kwargs["json"]
        configs = {c["settings_config_field_id"]: c["config_value"] for c in payload["settings_profile_configurations"]}
        workflow = json.loads(configs[_FIELD_EXTRACTION_WORKFLOW])
        stmt = workflow["statements"][0]
        assert "condition" in stmt
        qi = stmt["condition"]["query_items"][0]
        assert qi["value"] == "annotation.16"

    def test_payload_matches_real_api_format(self, mock_client):
        """Verify the payload shape exactly matches what the DXR API expects."""
        mock_client.patch.return_value = None
        items = [
            JsonSearchQueryItem(
                parameter="annotators",
                value="annotation.16",
                type="text",
                match_strategy="exists",
                operator="AND",
                group_id=0,
                group_order=0,
            )
        ]
        SettingsProfiles().set_extraction_workflow(
            profile_id=50217,
            enabled=True,
            steps=[WorkflowStep(extractor_id=594, condition=items)],
        )
        payload = mock_client.patch.call_args.kwargs["json"]

        # Top-level keys
        assert "profile_id" in payload
        assert "settings_profile_configurations" in payload

        # Both field IDs present
        field_ids = {c["settings_config_field_id"] for c in payload["settings_profile_configurations"]}
        assert _FIELD_EXTRACTION_ENABLED in field_ids
        assert _FIELD_EXTRACTION_WORKFLOW in field_ids

        # Enabled value is a lowercase string "true" / "false"
        configs = {c["settings_config_field_id"]: c["config_value"] for c in payload["settings_profile_configurations"]}
        assert configs[_FIELD_EXTRACTION_ENABLED] == "true"

        # Workflow value is a JSON string (not a dict)
        wf_value = configs[_FIELD_EXTRACTION_WORKFLOW]
        assert isinstance(wf_value, str)
        wf = json.loads(wf_value)
        assert "statements" in wf

    def test_disabled_with_no_steps(self, mock_client):
        mock_client.patch.return_value = None
        SettingsProfiles().set_extraction_workflow(
            profile_id=50217,
            enabled=False,
            steps=None,
        )
        payload = mock_client.patch.call_args.kwargs["json"]
        configs = {c["settings_config_field_id"]: c["config_value"] for c in payload["settings_profile_configurations"]}
        assert configs[_FIELD_EXTRACTION_ENABLED] == "false"
        workflow = json.loads(configs[_FIELD_EXTRACTION_WORKFLOW])
        assert workflow["statements"] == []

    def test_enabled_without_steps_raises(self, mock_client):
        with pytest.raises(ValueError, match="WorkflowStep"):
            SettingsProfiles().set_extraction_workflow(
                profile_id=50217,
                enabled=True,
                steps=[],
            )

    def test_multiple_steps(self, mock_client):
        mock_client.patch.return_value = None
        SettingsProfiles().set_extraction_workflow(
            profile_id=50217,
            enabled=True,
            steps=[WorkflowStep(extractor_id=1), WorkflowStep(extractor_id=2)],
        )
        payload = mock_client.patch.call_args.kwargs["json"]
        configs = {c["settings_config_field_id"]: c["config_value"] for c in payload["settings_profile_configurations"]}
        wf = json.loads(configs[_FIELD_EXTRACTION_WORKFLOW])
        assert len(wf["statements"]) == 2
        assert wf["statements"][0]["extractorId"] == 1
        assert wf["statements"][1]["extractorId"] == 2

    def test_uses_patch_endpoint(self, mock_client):
        mock_client.patch.return_value = None
        SettingsProfiles().set_extraction_workflow(
            profile_id=1,
            enabled=True,
            steps=[WorkflowStep(extractor_id=1)],
        )
        mock_client.patch.assert_called_once()
        url = mock_client.patch.call_args.args[0]
        assert url == "/api/settings-profiles/settings/config"


# ---------------------------------------------------------------------------
# SettingsProfiles.set_config
# ---------------------------------------------------------------------------

class TestSetConfig:
    def test_raw_config_patch(self, mock_client):
        mock_client.patch.return_value = None
        configurations = [{"settings_config_field_id": 99, "config_value": "some_value"}]
        SettingsProfiles().set_config(profile_id=50217, configurations=configurations)
        payload = mock_client.patch.call_args.kwargs["json"]
        assert payload["profile_id"] == 50217
        assert payload["settings_profile_configurations"] == configurations
