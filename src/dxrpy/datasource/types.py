from typing import TypedDict, List, Optional

class DataClass(TypedDict):
    description: str
    disable_category: bool
    name: str
    type: str
    id: Optional[int]

class Dictionary(DataClass):
    is_case_sensitive: bool
    values: List[str]

class NamedEntity(DataClass):
    class_name: str
    model_id: str

class Regex(DataClass):
    capturing_groups: str
    validator: Optional[str]
    value: str

class SettingsProfile(TypedDict):
    id: int
    name: str
    description: str
    disable_category: bool
    type: str
    access_level: Optional[str]
    datasources_count: Optional[int]

class Datasource(TypedDict):
    id: int
    name: str
    type: str
    description: Optional[str]
    disable_category: Optional[bool]
