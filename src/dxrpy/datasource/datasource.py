from typing import List, Dict, Union
from .types import DataClass, Dictionary, NamedEntity, Regex, SettingsProfile
from .ingester.datasource_ingester import DatasourceIngester
import requests


class Datasource:
    def __init__(
        self,
        billing_category: str,
        data_classes: List[Union[DataClass, Dictionary, NamedEntity, Regex]],
        datasource_connector_type_id: int,
        datasource_connector_type_name: str,
        id: int,
        metadata: Dict[str, str],
        monitorable: bool,
        name: str,
        settings_profile: SettingsProfile,
        status: str,
        base_url: str,
        session: requests.Session,
    ):
        self.billing_category = billing_category
        self.data_classes = data_classes
        self.datasource_connector_type_id = datasource_connector_type_id
        self.datasource_connector_type_name = datasource_connector_type_name
        self.id = id
        self.metadata = metadata
        self.monitorable = monitorable
        self.name = name
        self.settings_profile = settings_profile
        self.status = status
        self.base_url = base_url
        self.session = session

    def ingester(self) -> DatasourceIngester:
        """
        Returns a DatasourceIngester instance for this datasource.

        Returns:
            DatasourceIngester: The DatasourceIngester instance.
        """
        return DatasourceIngester(self.id)
