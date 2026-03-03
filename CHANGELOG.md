# Changelog

All notable changes to this project are documented here.

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
