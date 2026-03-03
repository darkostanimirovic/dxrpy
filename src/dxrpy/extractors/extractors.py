from __future__ import annotations

from typing import Any, Dict, List, Optional

from dxrpy.dxr_client import DXRHttpClient


class ExtractorInfo:
    """Lightweight representation of a metadata extractor returned by the API."""

    def __init__(self, data: Dict[str, Any]):
        self.id: int = data.get("id")
        self.name: str = data.get("name", "")
        self.description: Optional[str] = data.get("description")
        self.prompt: Optional[str] = data.get("prompt")
        self.data_types: List[str] = data.get("dataTypes") or []
        self.raw: Dict[str, Any] = data

    def __repr__(self) -> str:
        return f"ExtractorInfo(id={self.id}, name={self.name!r})"


class Extractors:
    """
    CRUD manager for DXR LLM metadata extractors.

    Extractors define a prompt template and a set of data types that the LLM
    should extract from a document. After creating an extractor, attach it to
    a datasource settings profile using
    :meth:`~dxrpy.settings_profiles.SettingsProfiles.set_extraction_workflow`.

    Access via ``DXRClient.extractors``.

    Example::

        client = DXRClient(api_url=..., api_key=...)
        extractor = client.extractors.create(
            name="PII extractor",
            prompt="Extract all personal information from the following text...",
            data_types=["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER"],
        )
    """

    def __init__(self):
        self.client: DXRHttpClient = DXRHttpClient.get_instance()

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def list(self) -> List[ExtractorInfo]:
        """Return all extractors visible to the authenticated user."""
        response = self.client.get("/api/extractors")
        items = response if isinstance(response, list) else response.get("content", response)
        return [ExtractorInfo(item) for item in items]

    def get(self, extractor_id: int) -> ExtractorInfo:
        """Fetch a single extractor by ID."""
        response = self.client.get(f"/api/extractors/{extractor_id}")
        return ExtractorInfo(response)

    def find_by_name(self, name: str) -> Optional[ExtractorInfo]:
        """Return the first extractor whose name matches exactly, or None."""
        for extractor in self.list():
            if extractor.name == name:
                return extractor
        return None

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def create(
        self,
        name: str,
        prompt: str,
        data_types: Optional[List[str]] = None,
        description: Optional[str] = None,
        **extra_fields,
    ) -> ExtractorInfo:
        """
        Create a new LLM metadata extractor.

        :param name: Display name for the extractor.
        :param prompt: The LLM prompt template used for extraction.
        :param data_types: List of data-type identifiers the extractor targets
            (e.g. ``["PERSON", "EMAIL_ADDRESS"]``).
        :param description: Optional description.
        :param extra_fields: Any additional fields forwarded to the API payload.
        :return: The created :class:`ExtractorInfo`.
        """
        payload: Dict[str, Any] = {
            "name": name,
            "prompt": prompt,
            **extra_fields,
        }
        if description is not None:
            payload["description"] = description
        if data_types is not None:
            payload["dataTypes"] = data_types

        response = self.client.post("/api/extractors", json=payload)
        return ExtractorInfo(response)

    def update(
        self,
        extractor_id: int,
        name: Optional[str] = None,
        prompt: Optional[str] = None,
        data_types: Optional[List[str]] = None,
        description: Optional[str] = None,
        **extra_fields,
    ) -> ExtractorInfo:
        """
        Update an existing extractor. Only supplied fields are sent.
        """
        payload: Dict[str, Any] = {**extra_fields}
        if name is not None:
            payload["name"] = name
        if prompt is not None:
            payload["prompt"] = prompt
        if description is not None:
            payload["description"] = description
        if data_types is not None:
            payload["dataTypes"] = data_types

        response = self.client.put(f"/api/extractors/{extractor_id}", json=payload)
        return ExtractorInfo(response)

    def delete(self, extractor_id: int) -> None:
        """Delete an extractor by ID."""
        self.client.delete(f"/api/extractors/{extractor_id}")
