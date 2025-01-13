from dxrpy.dxr_client import DXRHttpClient
from .index import Index

from .on_demand_classifier import OnDemandClassifier
from dotenv import load_dotenv
import os

load_dotenv()


class DXRClient:
    """
    DXRClient is a client for interacting with the DXR API.

    Attributes:
        base_url (str): The base URL for the DXR API.
        api_key (str): The API key for authenticating with the DXR API.
        _on_demand_classifier (OnDemandClassifier): Lazy-loaded on-demand classifier.
        _index (Index): Lazy-loaded index.
    """

    def __init__(self, api_url: str | None = None, api_key: str | None = None):
        """
        Initializes the DXRClient with the given base URL and API key.

        Args:
            base_url (str): The base URL for the DXR API.
            api_key (str): The API key for authenticating with the DXR API.
        """
        api_url = api_url or os.getenv("DXR_BASE_URL")
        api_key = api_key or os.getenv("DXR_API_KEY")

        if not api_url or not api_key:
            raise ValueError("api_url and api_key must be provided.")

        DXRHttpClient.get_instance(api_url, api_key)
        self._on_demand_classifier = None
        self._index = None

    @property
    def on_demand_classifier(self):
        """
        Lazy-loads and returns the on-demand classifier.

        Returns:
            OnDemandClassifier: The on-demand classifier.
        """
        if self._on_demand_classifier is None:
            self._on_demand_classifier = OnDemandClassifier()
        return self._on_demand_classifier

    @property
    def index(self):
        """
        Lazy-loads and returns the index.

        Returns:
            Index: The index.
        """
        if self._index is None:
            self._index = Index()
        return self._index
