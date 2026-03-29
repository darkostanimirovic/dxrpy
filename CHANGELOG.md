# Changelog

All notable changes to this project are documented here.

## [0.4.0] - 2026-03-29

### Added

- **Hit**: `tag_ids` property — returns smart-label tag IDs applied to a document.
- **Hit**: `annotator_ids()` method — returns the set of unique annotator IDs found in a document.
- **Hit**: `to_dict()` / `from_dict()` — serialize and reconstruct Hit objects for offline caching or analysis without an active DXR connection.
- **OnDemandClassifier**: `RunJobResult` dataclass returned by `run_job()`, carrying `hits`, `job`, and `scan_id` together.
- **OnDemandClassifier**: `run_job()` now accepts `timeout` (seconds), `page_size`, and auto-wraps `str`/`Path` inputs into `File` objects. Raises `TimeoutError` on deadline and `RuntimeError` on job failure.
- **DatasourceManager**: `find_by_connector_type(connector_type_id)` — find the first datasource with a given connector type.
- **DatasourceManager**: `find_by_name_prefix(prefix)` — list all datasources whose name starts with a prefix.
- **SettingsProfiles**: `get_data_classes(profile_id)` — retrieve data-class IDs configured on a profile.
- **SettingsProfiles**: `add_data_classes(profile_id, class_ids)` — add data-class IDs to a profile (idempotent).
- **Exports**: top-level `dxrpy` package now re-exports all public classes (`DXRClient`, `DXRHttpClient`, `Hit`, `OnDemandClassifier`, `RunJobResult`, `DatasourceManager`, `SettingsProfiles`, `SmartLabels`, `Extractors`, `File`, etc.) for convenient imports.
- **Tests**: added 36 new tests covering all additions (Hit serialization, OnDemandClassifier lifecycle, DatasourceManager filters, SettingsProfiles data classes).

### Fixed

- **Hit**: client is now lazily resolved, so `Hit.from_dict()` and `SearchResult` construction no longer require the `DXRHttpClient` singleton to be initialised upfront.
- **Exports**: `dxrpy.index`, `dxrpy.on_demand_classifier` sub-packages now properly export their public classes (previously empty `__init__.py` broke `from dxrpy.index import Hit` etc.).
- **DXRHttpClient**: `api_url` is now normalised to always end with `/api` on construction, so callers may pass either `https://host` or `https://host/api`. Resource classes no longer embed the `/api` prefix in every endpoint string.

### Changed

- **OnDemandClassifier**: `run_job()` now returns `RunJobResult` instead of `List[Hit]`. Access hits via `result.hits`.

## [0.3.3] - 2026-03-03

### Fixed

- **Datasources**: `create()` now defaults to `status="ENABLED"` so newly created datasources are immediately usable without a separate update call.

## [0.3.2] - 2026-03-03

### Fixed

- **Extractors**: correct endpoint (`/api/metadata-extractors`), `promptTemplate` field, single `dataType` enum (`TEXT`|`NUMBER`|`BOOLEAN`) replacing entity-type list, added `temperature` / `useDocumentContent` / `modelId` fields, `"type": "llm"` discriminator in payload, validation on create/update.
- **Datasources**: create now uses `/api/datasources/with-attributes`; required `DatasourceAttribute` list (`datasourceConnectorTypeAttributeId` + `value`); `update()` fetches current state before PUT.
- **Smart Labels**: `hexColor` field (no `#` prefix); `type` discriminator `"SMART"`/`"STANDARD"`; `savedQueryDtoList` structure with per-rule `datasourceIds`; new `SmartLabelRule` dataclass; `update()` uses `PUT /api/tags` with full body.
- **Settings Profiles**: `set_extraction_workflow` field IDs 21/22 flagged as pending DB migration.

## [0.3.1] - 2026-03-03

### Fixed

- Link `README.md` as PyPI project description via `readme` field in `pyproject.toml`.

## [0.3.0] - 2026-03-03

### Added

- **`DatasourceManager`** (`client.datasources`) — CRUD for datasources: `list()`, `get(id)`, `find_by_name(name)`, `create(...)`, `update(id, ...)`, `delete(id)`.
- **`SmartLabels`** (`client.smart_labels`) — CRUD for smart labels (tags): `list()`, `get(id)`, `find_by_name(name)`, `create(...)`, `update(id, ...)`, `delete(id)`. Supports attaching `JsonSearchQueryItem` conditions to trigger labels automatically.
- **`Extractors`** (`client.extractors`) — CRUD for LLM metadata extractors: `list()`, `get(id)`, `find_by_name(name)`, `create(...)`, `update(id, ...)`, `delete(id)`.
- **`SettingsProfiles`** (`client.settings_profiles`) — Settings profile management: `list()`, `get(id)`, `find_by_name(name)`, `set_extraction_workflow(profile_id, enabled, steps)`, `set_config(profile_id, configurations)`. The `set_extraction_workflow` helper encapsulates the `PATCH /api/settings-profiles/settings/config` call and accepts `WorkflowStep` objects.
- **`WorkflowStep`** dataclass — describes a single extractor step in a workflow definition, with an optional `JsonSearchQueryItem` condition list.
- `DXRHttpClient.patch()` method for `PATCH` requests.
- All four new managers are accessible as lazy-loaded properties on `DXRClient`.
- Exported `DatasourceInfo`, `DatasourceManager`, `ExtractorInfo`, `Extractors`, `SettingsProfileInfo`, `SettingsProfiles`, `SmartLabelInfo`, `SmartLabels`, `WorkflowStep` from the top-level `dxrpy` package.

### Fixed

- `DXRHttpClient.request()` now handles `204 No Content` responses correctly (previously raised `JSONDecodeError`).

### Changed

- `pytest` moved from runtime `dependencies` to `[project.optional-dependencies] dev` in `pyproject.toml`.

## [0.2.12] - 2024

- Initial public release with `OnDemandClassifier`, `Index`, `DocumentCategories`, and `DatasourceIngester`.
