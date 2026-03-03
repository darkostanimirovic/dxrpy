import os

from dotenv import load_dotenv

from dxrpy.dxr_client import DXRHttpClient
from .datasource import DatasourceManager
from .document_categories import DocumentCategories
from .extractors import Extractors
from .index import Index
from .on_demand_classifier import OnDemandClassifier
from .settings_profiles import SettingsProfiles
from .smart_labels import SmartLabels

load_dotenv()


class DXRClient:
    """
    DXRClient is a client for interacting with the DXR API.

    All sub-modules are lazy-loaded on first access:

    * :attr:`on_demand_classifier` — run ad-hoc classification jobs
    * :attr:`index` — search the DXR document index
    * :attr:`document_categories` — manage document categories
    * :attr:`datasources` — CRUD for datasources
    * :attr:`smart_labels` — CRUD for smart labels (tags)
    * :attr:`extractors` — CRUD for LLM metadata extractors
    * :attr:`settings_profiles` — manage settings profiles and extraction workflows
    """

    def __init__(
        self,
        api_url: str | None = None,
        api_key: str | None = None,
        ignore_ssl: bool = False,
    ):
        """
        Initialise the DXRClient.

        Credentials are resolved in order: explicit arguments → environment
        variables ``DXR_BASE_URL`` / ``DXR_API_KEY`` (loaded from ``.env``).

        Args:
            api_url: Base URL of the DXR API.
            api_key: API key for authentication.
            ignore_ssl: Disable SSL certificate verification (useful for
                self-signed certs on private deployments).
        """
        api_url = api_url or os.getenv("DXR_BASE_URL")
        api_key = api_key or os.getenv("DXR_API_KEY")

        if not api_url or not api_key:
            raise ValueError("api_url and api_key must be provided.")

        DXRHttpClient.get_instance(api_url, api_key, ignore_ssl)

        self._on_demand_classifier = None
        self._index = None
        self._document_categories = None
        self._datasources = None
        self._smart_labels = None
        self._extractors = None
        self._settings_profiles = None

    @property
    def on_demand_classifier(self) -> OnDemandClassifier:
        """Lazy-loaded on-demand classifier."""
        if self._on_demand_classifier is None:
            self._on_demand_classifier = OnDemandClassifier()
        return self._on_demand_classifier

    @property
    def index(self) -> Index:
        """Lazy-loaded document index."""
        if self._index is None:
            self._index = Index()
        return self._index

    @property
    def document_categories(self) -> DocumentCategories:
        """Lazy-loaded document categories manager."""
        if self._document_categories is None:
            self._document_categories = DocumentCategories()
        return self._document_categories

    @property
    def datasources(self) -> DatasourceManager:
        """Lazy-loaded datasource CRUD manager."""
        if self._datasources is None:
            self._datasources = DatasourceManager()
        return self._datasources

    @property
    def smart_labels(self) -> SmartLabels:
        """Lazy-loaded smart labels (tags) CRUD manager."""
        if self._smart_labels is None:
            self._smart_labels = SmartLabels()
        return self._smart_labels

    @property
    def extractors(self) -> Extractors:
        """Lazy-loaded LLM metadata extractor CRUD manager."""
        if self._extractors is None:
            self._extractors = Extractors()
        return self._extractors

    @property
    def settings_profiles(self) -> SettingsProfiles:
        """Lazy-loaded settings profile manager."""
        if self._settings_profiles is None:
            self._settings_profiles = SettingsProfiles()
        return self._settings_profiles
