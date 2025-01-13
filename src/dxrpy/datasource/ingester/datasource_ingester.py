from typing import Dict, List, Union, TypedDict

from dxrpy.dxr_client import DXRHttpClient


class DatasourceClass(TypedDict):
    class_id: int
    version: int
    is_synced: bool


class DatasourceIndexConfiguration(TypedDict):
    raw_text: str


class IndexStatusItem(TypedDict):
    index_name: str
    total_file_count: int
    composite_file_count: int
    total_sub_file_count: int
    indexed_data_object_count: int
    remote_data_object_count: int
    unreadable_file_count: int
    initial_index_is_complete: bool
    datasource_classes: List[DatasourceClass]
    datasource_index_configuration: DatasourceIndexConfiguration
    update_file_count: int
    crawl_active: bool
    datasource_id: int
    index_last_updated_date_time: str
    initial_index_start_date_time: str
    initial_index_initialization_duration: str


class IndexStatusResponse(TypedDict):
    items: List[IndexStatusItem]


class DatasourceIngester:
    def __init__(self, datasource_id: int):
        self.datasource_id = datasource_id
        self.client = DXRHttpClient.get_instance()

    def index_status(self) -> Union[IndexStatusResponse, Dict]:
        response = self.client.get(
            f"/datasources/ingester/{self.datasource_id}/index/status"
        )
        return response
