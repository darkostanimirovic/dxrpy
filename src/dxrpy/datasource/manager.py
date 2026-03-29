from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from dxrpy.dxr_client import DXRHttpClient


@dataclass
class DatasourceAttribute:
    """
    A connector-type attribute value, required when creating a datasource.

    :param attribute_type_id: The ``datasourceConnectorTypeAttributeId`` for
        this attribute (defined by the connector type).
    :param value: The attribute value as a string.
    """

    attribute_type_id: int
    value: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "datasourceConnectorTypeAttributeId": self.attribute_type_id,
            "value": self.value,
        }


class DatasourceInfo:
    """Lightweight representation of a datasource returned by the API."""

    def __init__(self, data: Dict[str, Any]):
        self.id: int = data.get("id")
        self.name: str = data.get("name", "")
        self.status: str = data.get("status", "")
        self.connector_type_id: Optional[int] = data.get("datasourceConnectorTypeId")
        self.connector_type_name: Optional[str] = data.get("datasourceConnectorTypeName")
        self.settings_profile_id: Optional[int] = (
            (data.get("settingsProfile") or {}).get("id")
        )
        self.raw: Dict[str, Any] = data

    def __repr__(self) -> str:
        return f"DatasourceInfo(id={self.id}, name={self.name!r}, status={self.status!r})"


class DatasourceManager:
    """
    CRUD manager for DXR datasources.

    Access via ``DXRClient.datasources``.

    Example::

        client = DXRClient(api_url=..., api_key=...)
        ds = client.datasources.create(
            name="benchmark-experiment-1",
            connector_type_id=7,
            attributes=[DatasourceAttribute(attribute_type_id=12, value="/data")],
            settings_profile_id=50217,
        )
        print(ds.id)
    """

    def __init__(self):
        self.client: DXRHttpClient = DXRHttpClient.get_instance()

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def list(self) -> List[DatasourceInfo]:
        """Return all datasources visible to the authenticated user."""
        response = self.client.get("/datasources")
        items = response if isinstance(response, list) else response.get("content", response)
        return [DatasourceInfo(item) for item in items]

    def get(self, datasource_id: int) -> DatasourceInfo:
        """Fetch a single datasource by ID.

        Falls back to the list endpoint when the single-item endpoint
        is not available (older DXR versions).
        """
        try:
            response = self.client.get(f"/datasources/{datasource_id}")
            return DatasourceInfo(response)
        except Exception:
            # Fallback: filter from the full list
            for ds in self.list():
                if ds.id == datasource_id:
                    return ds
            raise ValueError(f"Datasource {datasource_id} not found")

    def find_by_name(self, name: str) -> Optional[DatasourceInfo]:
        """Return the first datasource whose name matches exactly, or None."""
        for ds in self.list():
            if ds.name == name:
                return ds
        return None

    def find_by_connector_type(self, connector_type_id: int) -> Optional[DatasourceInfo]:
        """Return the first datasource with the given connector type, or None."""
        for ds in self.list():
            if ds.connector_type_id == connector_type_id:
                return ds
        return None

    def find_by_name_prefix(self, prefix: str) -> List[DatasourceInfo]:
        """Return all datasources whose name starts with *prefix*."""
        return [ds for ds in self.list() if ds.name.startswith(prefix)]

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def create(
        self,
        name: str,
        connector_type_id: int,
        attributes: List[DatasourceAttribute],
        settings_profile_id: Optional[int] = None,
        description: Optional[str] = None,
        status: str = "ENABLED",
        **extra_fields,
    ) -> DatasourceInfo:
        """
        Create a new datasource.

        Some connector types (e.g. On-Demand Classifier) have no required
        attributes and accept an empty *attributes* list.

        :param name: Human-readable name.
        :param connector_type_id: Connector type ID
            (``datasourceConnectorTypeId``).
        :param attributes: :class:`DatasourceAttribute` objects describing
            the connector configuration.  May be empty for connector types
            that have no required attributes.
        :param settings_profile_id: Optional settings profile to attach.
        :param description: Optional description.
        :param status: Datasource status. Defaults to ``"ENABLED"`` so the
            datasource is immediately usable after creation.
        :param extra_fields: Any additional fields forwarded to the payload.
        :return: The created :class:`DatasourceInfo`.
        """
        payload: Dict[str, Any] = {
            "name": name,
            "datasourceConnectorTypeId": connector_type_id,
            "status": status,
            "datasourceAttributesDTOList": [a.to_dict() for a in attributes],
            **extra_fields,
        }
        if description is not None:
            payload["description"] = description
        if settings_profile_id is not None:
            payload["settingsProfileId"] = settings_profile_id

        response = self.client.post("/datasources/with-attributes", json=payload)
        return DatasourceInfo(response)

    def update(
        self,
        datasource_id: int,
        name: Optional[str] = None,
        settings_profile_id: Optional[int] = None,
        description: Optional[str] = None,
        **extra_fields,
    ) -> DatasourceInfo:
        """
        Update an existing datasource.

        This calls ``PUT /api/datasources``. The backend requires the full
        datasource object, so this method fetches the current state first
        and merges your changes on top.
        """
        current = self.get(datasource_id)
        payload: Dict[str, Any] = {
            **current.raw,
            **extra_fields,
        }
        if name is not None:
            payload["name"] = name
        if description is not None:
            payload["description"] = description
        if settings_profile_id is not None:
            payload["settingsProfileId"] = settings_profile_id

        response = self.client.put("/datasources", json=payload)
        return DatasourceInfo(response)

    def delete(self, datasource_id: int) -> None:
        """Delete a datasource by ID."""
        self.client.delete(f"/datasources/{datasource_id}")
