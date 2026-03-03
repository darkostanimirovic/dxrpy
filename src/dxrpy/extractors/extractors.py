from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from dxrpy.dxr_client import DXRHttpClient

# Valid output data types as defined by the backend DataType enum
DataType = Literal["TEXT", "NUMBER", "BOOLEAN"]
DATA_TYPES: tuple[str, ...] = ("TEXT", "NUMBER", "BOOLEAN")


class ExtractorInfo:
    """Lightweight representation of a metadata extractor returned by the API."""

    def __init__(self, data: Dict[str, Any]):
        self.id: int = data.get("id")
        self.name: str = data.get("name", "")
        self.description: Optional[str] = data.get("description")
        self.prompt_template: Optional[str] = data.get("promptTemplate")
        self.data_type: Optional[str] = data.get("dataType")
        self.temperature: float = data.get("temperature", 0.7)
        self.use_document_content: bool = data.get("useDocumentContent", False)
        self.model_id: Optional[str] = data.get("modelId")
        self.raw: Dict[str, Any] = data

    def __repr__(self) -> str:
        return f"ExtractorInfo(id={self.id}, name={self.name!r}, data_type={self.data_type!r})"


class Extractors:
    """
    CRUD manager for DXR LLM metadata extractors.

    Each extractor defines a prompt template and a single output data type
    (``TEXT``, ``NUMBER``, or ``BOOLEAN``). The prompt template should
    reference ``{{document_text}}`` where the document content will be
    injected at runtime.

    After creating an extractor, attach it to a datasource settings profile
    via
    :meth:`~dxrpy.settings_profiles.SettingsProfiles.set_extraction_workflow`.

    Access via ``DXRClient.extractors``.

    Example::

        client = DXRClient(api_url=..., api_key=...)
        extractor = client.extractors.create(
            name="Employment status",
            prompt_template=(
                "From the following document extract whether the person is "
                "currently employed. Answer only true or false.\\n\\n"
                "{{document_text}}"
            ),
            data_type="BOOLEAN",
        )
        print(extractor.id)
    """

    def __init__(self):
        self.client: DXRHttpClient = DXRHttpClient.get_instance()

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def list(self) -> List[ExtractorInfo]:
        """Return all extractors visible to the authenticated user."""
        response = self.client.get("/api/metadata-extractors")
        items = response if isinstance(response, list) else response.get("content", response)
        return [ExtractorInfo(item) for item in items]

    def get(self, extractor_id: int) -> ExtractorInfo:
        """Fetch a single extractor by ID."""
        response = self.client.get(f"/api/metadata-extractors/{extractor_id}")
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
        prompt_template: str,
        data_type: DataType,
        description: str = "",
        temperature: float = 0.7,
        use_document_content: bool = False,
        model_id: Optional[str] = None,
        **extra_fields,
    ) -> ExtractorInfo:
        """
        Create a new LLM metadata extractor.

        :param name: Display name (1–255 characters, required).
        :param prompt_template: The prompt sent to the LLM. Use
            ``{{document_text}}`` as the placeholder for document content.
            Maximum 4096 characters.
        :param data_type: The output type the extractor produces.
            Must be one of ``"TEXT"``, ``"NUMBER"``, or ``"BOOLEAN"``.
        :param description: Optional description (max 4096 characters).
        :param temperature: LLM temperature (0.0–2.0, default 0.7).
        :param use_document_content: Whether to inject document content
            automatically (default ``False``).
        :param model_id: Optional UUID of a configured LLM model.
        :param extra_fields: Any additional fields forwarded to the payload.
        :return: The created :class:`ExtractorInfo`.
        :raises ValueError: If *data_type* is not a valid value.
        """
        if data_type not in DATA_TYPES:
            raise ValueError(
                f"Invalid data_type {data_type!r}. Must be one of: {', '.join(DATA_TYPES)}"
            )

        payload: Dict[str, Any] = {
            "type": "llm",
            "name": name,
            "description": description,
            "promptTemplate": prompt_template,
            "dataType": data_type,
            "temperature": temperature,
            "useDocumentContent": use_document_content,
            **extra_fields,
        }
        if model_id is not None:
            payload["modelId"] = model_id

        response = self.client.post("/api/metadata-extractors", json=payload)
        return ExtractorInfo(response)

    def update(
        self,
        extractor_id: int,
        name: Optional[str] = None,
        prompt_template: Optional[str] = None,
        data_type: Optional[DataType] = None,
        description: Optional[str] = None,
        temperature: Optional[float] = None,
        use_document_content: Optional[bool] = None,
        model_id: Optional[str] = None,
        **extra_fields,
    ) -> ExtractorInfo:
        """
        Update an existing extractor.

        The backend requires the full object on PUT, so this method fetches
        the current state first and merges your changes on top.

        :raises ValueError: If *data_type* is provided but not a valid value.
        """
        if data_type is not None and data_type not in DATA_TYPES:
            raise ValueError(
                f"Invalid data_type {data_type!r}. Must be one of: {', '.join(DATA_TYPES)}"
            )

        current = self.get(extractor_id)
        payload: Dict[str, Any] = {
            **current.raw,
            **extra_fields,
        }
        if name is not None:
            payload["name"] = name
        if description is not None:
            payload["description"] = description
        if prompt_template is not None:
            payload["promptTemplate"] = prompt_template
        if data_type is not None:
            payload["dataType"] = data_type
        if temperature is not None:
            payload["temperature"] = temperature
        if use_document_content is not None:
            payload["useDocumentContent"] = use_document_content
        if model_id is not None:
            payload["modelId"] = model_id

        response = self.client.put(f"/api/metadata-extractors/{extractor_id}", json=payload)
        return ExtractorInfo(response)

    def delete(self, extractor_id: int) -> None:
        """Delete an extractor by ID."""
        self.client.delete(f"/api/metadata-extractors/{extractor_id}")
