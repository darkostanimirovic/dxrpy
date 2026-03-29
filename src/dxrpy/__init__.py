"""dxrpy — Python client library for Data X-Ray."""

from .client import DXRClient
from .dxr_client import DXRHttpClient

# Sub-module re-exports for convenience
from .datasource import DatasourceAttribute, DatasourceInfo, DatasourceManager
from .document_categories import DocumentCategories, DocumentCategory
from .extractors import DATA_TYPES, DataType, ExtractorInfo, Extractors
from .index import (
    Annotation,
    Annotator,
    Hit,
    Index,
    JsonSearchQuery,
    JsonSearchQueryItem,
    Label,
    SearchResult,
)
from .on_demand_classifier import (
    OnDemandClassifier,
    OnDemandClassifierJob,
    RunJobResult,
)
from .settings_profiles import (
    SettingsProfileInfo,
    SettingsProfiles,
    WorkflowStep,
)
from .smart_labels import SmartLabelInfo, SmartLabelRule, SmartLabels
from .utils import File
