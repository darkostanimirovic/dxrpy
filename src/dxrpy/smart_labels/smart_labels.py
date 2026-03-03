from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from dxrpy.dxr_client import DXRHttpClient
from dxrpy.index.json_search_query import JsonSearchQueryItem


@dataclass
class SmartLabelRule:
    """
    One saved-query rule within a smart label.

    A smart label can contain multiple rules, each targeting a different set
    of datasources or using different query conditions.

    :param datasource_ids: Datasources this rule applies to.
    :param query_items: Query conditions that trigger the label.
    :param status: ``"RUNNING"`` (active) or ``"PAUSED"``.
    """

    datasource_ids: List[int]
    query_items: List[JsonSearchQueryItem] = field(default_factory=list)
    status: str = "RUNNING"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": {"query_items": [item.to_dict() for item in self.query_items]},
            "datasourceIds": self.datasource_ids,
            "status": self.status,
        }


class SmartLabelInfo:
    """Lightweight representation of a smart label (tag) returned by the API."""

    def __init__(self, data: Dict[str, Any]):
        self.id: int = data.get("id")
        self.name: str = data.get("name", "")
        self.hex_color: Optional[str] = data.get("hexColor")
        self.type: str = data.get("type", "STANDARD")
        self.raw: Dict[str, Any] = data

    def __repr__(self) -> str:
        return f"SmartLabelInfo(id={self.id}, name={self.name!r}, type={self.type!r})"


class SmartLabels:
    """
    CRUD manager for DXR smart labels (tags).

    Smart labels automatically tag documents matching a query condition.
    Standard labels (``type="STANDARD"``) are applied manually; smart labels
    (``type="SMART"``) fire automatically based on saved-query rules.

    Access via ``DXRClient.smart_labels``.

    Example::

        client = DXRClient(api_url=..., api_key=...)

        # Standard tag (manual)
        tag = client.smart_labels.create(name="Reviewed", hex_color="3498DB")

        # Smart label that fires whenever an SSN annotation exists
        label = client.smart_labels.create(
            name="Has-SSN",
            hex_color="E74C3C",
            rules=[
                SmartLabelRule(
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
        hex_color: str,
        rules: Optional[List[SmartLabelRule]] = None,
        description: Optional[str] = None,
        **extra_fields,
    ) -> SmartLabelInfo:
        """
        Create a new smart label.

        When *rules* are provided the label is created with
        ``type="SMART"`` and the rules are stored as ``savedQueryDtoList``.
        Without rules the label is a plain ``"STANDARD"`` tag.

        :param name: Display name (must be unique).
        :param hex_color: Hex colour string **without** the ``#`` prefix,
            e.g. ``"E74C3C"``.
        :param rules: Optional list of :class:`SmartLabelRule` objects.
        :param description: Optional description.
        :param extra_fields: Any additional fields forwarded to the payload.
        :return: The created :class:`SmartLabelInfo`.
        """
        payload: Dict[str, Any] = {
            "name": name,
            "hexColor": hex_color,
            "type": "SMART" if rules else "STANDARD",
            **extra_fields,
        }
        if description is not None:
            payload["description"] = description
        if rules:
            payload["savedQueryDtoList"] = [r.to_dict() for r in rules]

        response = self.client.post("/api/tags", json=payload)
        return SmartLabelInfo(response)

    def update(
        self,
        label_id: int,
        name: Optional[str] = None,
        hex_color: Optional[str] = None,
        rules: Optional[List[SmartLabelRule]] = None,
        description: Optional[str] = None,
        **extra_fields,
    ) -> SmartLabelInfo:
        """
        Update an existing smart label.

        The backend requires the full tag object on ``PUT /api/tags``, so this
        method fetches the current state first and merges your changes.
        """
        current = self.get(label_id)
        payload: Dict[str, Any] = {
            **current.raw,
            **extra_fields,
        }
        if name is not None:
            payload["name"] = name
        if hex_color is not None:
            payload["hexColor"] = hex_color
        if description is not None:
            payload["description"] = description
        if rules is not None:
            payload["savedQueryDtoList"] = [r.to_dict() for r in rules]
            payload["type"] = "SMART" if rules else "STANDARD"

        response = self.client.put("/api/tags", json=payload)
        return SmartLabelInfo(response)

    def delete(self, label_id: int) -> None:
        """Delete a smart label by ID."""
        self.client.delete(f"/api/tags/{label_id}")
