from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from dxrpy.dxr_client import DXRHttpClient
from dxrpy.index.json_search_query import JsonSearchQueryItem

# Settings config field IDs for the LLM extraction workflow.
# NOTE: As of the current schema, fields 21 and 22 are not yet present in the
# database.  A Liquibase migration must be run to add them before these
# constants (and set_extraction_workflow) will work.  Update the values below
# once the migration is merged and the correct IDs are confirmed.
_FIELD_EXTRACTION_ENABLED = 21   # pending DB migration
_FIELD_EXTRACTION_WORKFLOW = 22  # pending DB migration


@dataclass
class WorkflowStep:
    """
    One statement in an extractor workflow definition.

    :param extractor_id: ID of the :class:`~dxrpy.extractors.ExtractorInfo` to run.
    :param condition: Optional list of query conditions. When provided the extractor
        only runs on documents that match **all** conditions. When omitted the extractor
        runs unconditionally on every document.
    """

    extractor_id: int
    condition: List[JsonSearchQueryItem] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        stmt: Dict[str, Any] = {
            "type": "extractor",
            "extractorId": self.extractor_id,
        }
        if self.condition:
            stmt["condition"] = {
                "query_items": [item.to_dict() for item in self.condition]
            }
        return stmt


class SettingsProfileInfo:
    """Lightweight representation of a settings profile returned by the API."""

    def __init__(self, data: Dict[str, Any]):
        self.id: int = data.get("id")
        self.name: str = data.get("name", "")
        self.description: Optional[str] = data.get("description")
        self.type: Optional[str] = data.get("type")
        self.raw: Dict[str, Any] = data

    def __repr__(self) -> str:
        return f"SettingsProfileInfo(id={self.id}, name={self.name!r})"


class SettingsProfiles:
    """
    Manager for DXR settings profiles.

    Settings profiles bundle classification configuration (data classes, LLM
    extractors, thresholds, etc.) and can be attached to one or more datasources.

    The main high-level helper is :meth:`set_extraction_workflow`, which
    configures the LLM extractor workflow for a specific profile in a single call.

    Access via ``DXRClient.settings_profiles``.

    Example::

        client = DXRClient(api_url=..., api_key=...)

        # Enable extraction and attach an extractor that always runs
        client.settings_profiles.set_extraction_workflow(
            profile_id=50217,
            enabled=True,
            steps=[WorkflowStep(extractor_id=594)],
        )

        # Extractor that only fires when an SSN annotation already exists
        from dxrpy.index.json_search_query import JsonSearchQueryItem
        client.settings_profiles.set_extraction_workflow(
            profile_id=50217,
            enabled=True,
            steps=[
                WorkflowStep(
                    extractor_id=594,
                    condition=[
                        JsonSearchQueryItem(
                            parameter="annotators",
                            value="annotation.16",
                            type="text",
                            match_strategy="exists",
                        )
                    ],
                )
            ],
        )
    """

    def __init__(self):
        self.client: DXRHttpClient = DXRHttpClient.get_instance()

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def list(self) -> List[SettingsProfileInfo]:
        """Return all settings profiles visible to the authenticated user."""
        response = self.client.get("/settings-profiles")
        items = response if isinstance(response, list) else response.get("content", response)
        return [SettingsProfileInfo(item) for item in items]

    def get(self, profile_id: int) -> SettingsProfileInfo:
        """Fetch a single settings profile by ID."""
        response = self.client.get(f"/settings-profiles/{profile_id}")
        return SettingsProfileInfo(response)

    def find_by_name(self, name: str) -> Optional[SettingsProfileInfo]:
        """Return the first settings profile whose name matches exactly, or None."""
        for profile in self.list():
            if profile.name == name:
                return profile
        return None

    # ------------------------------------------------------------------
    # Data classes (annotator configuration)
    # ------------------------------------------------------------------

    def get_data_classes(self, profile_id: int) -> List[int]:
        """Return the list of data-class IDs configured on a profile.

        Data classes control which annotators (regex, dictionary, NER, etc.)
        run during document scans for datasources linked to this profile.
        """
        response = self.client.get(
            f"/settings-profiles/{profile_id}/data-classes"
        )
        return list(response) if isinstance(response, list) else []

    def add_data_classes(self, profile_id: int, class_ids: List[int]) -> None:
        """Add data-class IDs to a settings profile.

        Idempotent — IDs already present are silently ignored by the backend.

        :param profile_id: Target settings profile.
        :param class_ids: Data-class IDs to add (e.g. annotator IDs for
            regex or dictionary classifiers).
        """
        self.client.post(
            f"/settings-profiles/{profile_id}/add-data-classes",
            json=class_ids,
        )

    # ------------------------------------------------------------------
    # Extraction workflow
    # ------------------------------------------------------------------

    def set_extraction_workflow(
        self,
        profile_id: int,
        enabled: bool,
        steps: Optional[List[WorkflowStep]] = None,
    ) -> None:
        """
        Configure the LLM metadata extraction workflow for a settings profile.

        This is a convenience wrapper around the low-level
        ``PATCH /api/settings-profiles/settings/config`` endpoint that builds
        the correct payload from a list of :class:`WorkflowStep` objects.

        :param profile_id: ID of the target settings profile.
        :param enabled: Whether to enable metadata extraction on this profile.
        :param steps: Ordered list of :class:`WorkflowStep` instances defining
            which extractors run and under what conditions. Required when
            *enabled* is ``True``.
        :raises ValueError: If *enabled* is ``True`` but no *steps* are provided.
        """
        if enabled and not steps:
            raise ValueError("At least one WorkflowStep is required when enabled=True.")

        workflow_json = json.dumps(
            {"statements": [step.to_dict() for step in (steps or [])]}
        )

        payload = {
            "profile_id": profile_id,
            "settings_profile_configurations": [
                {
                    "settings_config_field_id": _FIELD_EXTRACTION_WORKFLOW,
                    "config_value": workflow_json,
                },
                {
                    "settings_config_field_id": _FIELD_EXTRACTION_ENABLED,
                    "config_value": str(enabled).lower(),
                },
            ],
        }

        self.client.patch("/settings-profiles/settings/config", json=payload)

    # ------------------------------------------------------------------
    # Raw config access
    # ------------------------------------------------------------------

    def set_config(
        self,
        profile_id: int,
        configurations: List[Dict[str, Any]],
    ) -> None:
        """
        Low-level helper to patch arbitrary settings profile config fields.

        :param profile_id: ID of the target settings profile.
        :param configurations: List of ``{"settings_config_field_id": int,
            "config_value": str}`` dicts matching the API payload format.
        """
        payload = {
            "profile_id": profile_id,
            "settings_profile_configurations": configurations,
        }
        self.client.patch("/settings-profiles/settings/config", json=payload)
