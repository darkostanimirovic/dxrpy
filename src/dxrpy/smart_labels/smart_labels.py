from __future__ import annotations

from typing import Any, Dict, List, Optional

from dxrpy.dxr_client import DXRHttpClient
from dxrpy.index.json_search_query import JsonSearchQueryItem


class SmartLabelInfo:
    """Lightweight representation of a smart label (tag) returned by the API."""

    def __init__(self, data: Dict[str, Any]):
        self.id: int = data.get("id")
        self.name: str = data.get("name", "")
        self.color: Optional[str] = data.get("color")
        self.datasource_ids: List[int] = data.get("datasourceIds") or []
        self.raw: Dict[str, Any] = data

    def __repr__(self) -> str:
        return f"SmartLabelInfo(id={self.id}, name={self.name!r})"


class SmartLabels:
    """
    CRUD manager for DXR smart labels (tags).

    Smart labels are global rules that automatically tag documents matching
    a query condition. Unlike extractors, they are not bound to a specific
    datasource at creation time — instead you specify which datasource(s)
    they should apply to.

    Access via ``DXRClient.smart_labels``.

    Example::

        client = DXRClient(api_url=..., api_key=...)
        label = client.smart_labels.create(
            name="Has-SSN",
            datasource_ids=[50148],
            query_items=[
                JsonSearchQueryItem(
                    parameter="annotators",
                    value="annotation.42",
                    type="text",
                    match_strategy="exists",
                ),
            ],
        )
    """

    def __init__(self):
        self.client: DXRHttpClient = DXRHttpClient.get_instance()

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def list(self) -> List[SmartLabelInfo]:
        """Return all smart labels visible to the authenticated user."""
        response = self.client.get("/api/tags")
        items = response if isinstance(response, list) else response.get("content", response)
        return [SmartLabelInfo(item) for item in items]

    def get(self, label_id: int) -> SmartLabelInfo:
        """Fetch a single smart label by ID."""
        response = self.client.get(f"/api/tags/{label_id}")
        return SmartLabelInfo(response)

    def find_by_name(self, name: str) -> Optional[SmartLabelInfo]:
        """Return the first smart label whose name matches exactly, or None."""
        for label in self.list():
            if label.name == name:
                return label
        return None

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def create(
        self,
        name: str,
        datasource_ids: List[int],
        query_items: Optional[List[JsonSearchQueryItem]] = None,
        color: Optional[str] = None,
        **extra_fields,
    ) -> SmartLabelInfo:
        """
        Create a new smart label.

        :param name: Display name for the label.
        :param datasource_ids: Datasource(s) this label should apply to.
        :param query_items: Query conditions that trigger the label.
            If omitted, the label is created with no conditions (matches nothing).
        :param color: Optional hex colour string (e.g. ``"#FF5733"``).
        :param extra_fields: Any additional fields forwarded to the API payload.
        :return: The created :class:`SmartLabelInfo`.
        """
        payload: Dict[str, Any] = {
            "name": name,
            "datasourceIds": datasource_ids,
            **extra_fields,
        }
        if color is not None:
            payload["color"] = color
        if query_items is not None:
            payload["savedQuery"] = {
                "query_items": [item.to_dict() for item in query_items]
            }

        response = self.client.post("/api/tags", json=payload)
        return SmartLabelInfo(response)

    def update(
        self,
        label_id: int,
        name: Optional[str] = None,
        datasource_ids: Optional[List[int]] = None,
        query_items: Optional[List[JsonSearchQueryItem]] = None,
        color: Optional[str] = None,
        **extra_fields,
    ) -> SmartLabelInfo:
        """
        Update an existing smart label. Only supplied fields are sent.
        """
        payload: Dict[str, Any] = {**extra_fields}
        if name is not None:
            payload["name"] = name
        if color is not None:
            payload["color"] = color
        if datasource_ids is not None:
            payload["datasourceIds"] = datasource_ids
        if query_items is not None:
            payload["savedQuery"] = {
                "query_items": [item.to_dict() for item in query_items]
            }

        response = self.client.put(f"/api/tags/{label_id}", json=payload)
        return SmartLabelInfo(response)

    def delete(self, label_id: int) -> None:
        """Delete a smart label by ID."""
        self.client.delete(f"/api/tags/{label_id}")
