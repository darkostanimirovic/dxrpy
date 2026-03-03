from __future__ import annotations

from typing import Any, Dict, List, Optional

from dxrpy.dxr_client import DXRHttpClient


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
            connector_type_id=7,          # on-demand / file upload connector
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
        response = self.client.get("/api/datasources")
        # API may return a list directly or a paged envelope
        items = response if isinstance(response, list) else response.get("content", response)
        return [DatasourceInfo(item) for item in items]

    def get(self, datasource_id: int) -> DatasourceInfo:
        """Fetch a single datasource by ID."""
        response = self.client.get(f"/api/datasources/{datasource_id}")
        return DatasourceInfo(response)

    def find_by_name(self, name: str) -> Optional[DatasourceInfo]:
        """Return the first datasource whose name matches exactly, or None."""
        for ds in self.list():
            if ds.name == name:
                return ds
        return None

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def create(
        self,
        name: str,
        connector_type_id: int,
        settings_profile_id: Optional[int] = None,
        description: Optional[str] = None,
        **extra_fields,
    ) -> DatasourceInfo:
        """
        Create a new datasource.

        :param name: Human-readable name.
        :param connector_type_id: Connector type (e.g. 7 for on-demand file upload).
        :param settings_profile_id: Optional settings profile to attach.
        :param description: Optional description.
        :param extra_fields: Any additional fields forwarded to the API payload.
        :return: The created :class:`DatasourceInfo`.
        """
        payload: Dict[str, Any] = {
            "name": name,
            "datasourceConnectorTypeId": connector_type_id,
            **extra_fields,
        }
        if description is not None:
            payload["description"] = description
        if settings_profile_id is not None:
            payload["settingsProfileId"] = settings_profile_id

        response = self.client.post("/api/datasources", json=payload)
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

        Only supplied fields are included in the request body.
        """
        payload: Dict[str, Any] = {**extra_fields}
        if name is not None:
            payload["name"] = name
        if description is not None:
            payload["description"] = description
        if settings_profile_id is not None:
            payload["settingsProfileId"] = settings_profile_id

        response = self.client.put(f"/api/datasources/{datasource_id}", json=payload)
        return DatasourceInfo(response)

    def delete(self, datasource_id: int) -> None:
        """Delete a datasource by ID."""
        self.client.delete(f"/api/datasources/{datasource_id}")
