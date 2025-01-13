from typing import Any, Dict, List, Optional


class JsonSearchQueryItem:
    def __init__(
        self,
        parameter: str,
        value: Any,
        type: str,
        match_strategy: str = "exact",
        operator: str = "AND",
        group_id: int = 0,
        group_order: int = 0,
    ):
        self.parameter = parameter
        self.value = value
        self.type = type
        self.match_strategy = match_strategy
        self.operator = operator
        self.group_id = group_id
        self.group_order = group_order

    def to_dict(self) -> Dict[str, Any]:
        return {
            "parameter": self.parameter,
            "value": self.value,
            "type": self.type,
            "match_strategy": self.match_strategy,
            "operator": self.operator,
            "group_id": self.group_id,
            "group_order": self.group_order,
        }


class JsonSearchQuery:
    def __init__(
        self,
        datasource_ids: Optional[List[str]] = None,
        page_number: int = 0,
        page_size: int = 20,
        query_items: Optional[List[JsonSearchQueryItem]] = None,
    ):
        self.datasource_ids = datasource_ids or []
        self.page_number = page_number
        self.page_size = page_size
        self.query_items = query_items or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mode": "DXR_JSON_QUERY",
            "datasourceIds": self.datasource_ids,
            "pageNumber": self.page_number,
            "pageSize": self.page_size,
            "filter": {"query_items": [item.to_dict() for item in self.query_items]},
        }
