# Data X-Ray Python Library

Unofficial Python library for the Data X-Ray API.

> **Warning**
> This library is unofficial and unsupported and may change at any time. Not for production use.

## Installation

```sh
pip install dxrpy
```

## Usage

### Initializing the Client

```python
from dxrpy import DXRClient

client = DXRClient(
    api_url="https://your-dxr-instance.example.com",
    api_key="your_api_key",
)
```

Credentials can also be loaded from environment variables (or a `.env` file):

```
DXR_BASE_URL=https://your-dxr-instance.example.com
DXR_API_KEY=your_api_key
```

---

### On-Demand Classifier

Run files through the on-demand classification pipeline.

```python
from dxrpy.utils import File

files = [File("path/to/file1.txt"), File("path/to/file2.txt")]
result = client.on_demand_classifier.run_job(files, datasource_id=123)

for hit in result.hits:
    print(hit.file_name, hit.labels)
```

---

### Datasources

Create and manage datasources programmatically.

```python
# List all datasources
datasources = client.datasources.list()

# Create a new datasource
ds = client.datasources.create(
    name="benchmark-experiment-1",
    connector_type_id=7,          # on-demand / file upload connector
    settings_profile_id=50217,
)
print(ds.id)

# Find by name
ds = client.datasources.find_by_name("benchmark-experiment-1")

# Update
client.datasources.update(ds.id, name="benchmark-experiment-1-v2")

# Delete
client.datasources.delete(ds.id)
```

---

### Smart Labels

Smart labels (tags) automatically tag documents matching a query condition.
They are defined globally and reference one or more datasources.

```python
from dxrpy.index.json_search_query import JsonSearchQueryItem

# Create a label that fires whenever an SSN annotation exists
label = client.smart_labels.create(
    name="Has-SSN",
    datasource_ids=[50148],
    query_items=[
        JsonSearchQueryItem(
            parameter="annotators",
            value="annotation.42",
            type="text",
            match_strategy="exists",
        ),
    ],
    color="#FF5733",
)

# List / find
labels = client.smart_labels.list()
label = client.smart_labels.find_by_name("Has-SSN")

# Update conditions
client.smart_labels.update(label.id, query_items=[...])

# Delete
client.smart_labels.delete(label.id)
```

---

### Extractors

LLM metadata extractors define a prompt and optional target data types.

```python
extractor = client.extractors.create(
    name="PII extractor",
    prompt_template="Extract all personal information from: {{document_text}}",
    data_type="TEXT",
)
print(extractor.id)

# CRUD
extractors = client.extractors.list()
extractor = client.extractors.find_by_name("PII extractor")
client.extractors.update(extractor.id, prompt_template="Updated prompt...")
client.extractors.delete(extractor.id)
```

---

### Settings Profiles & Extraction Workflows

Settings profiles bundle classification configuration. Use `set_extraction_workflow`
to attach an extractor (unconditionally or with conditions) to a profile.

```python
from dxrpy import WorkflowStep
from dxrpy.index.json_search_query import JsonSearchQueryItem

# Extractor that always runs
client.settings_profiles.set_extraction_workflow(
    profile_id=50217,
    enabled=True,
    steps=[WorkflowStep(extractor_id=594)],
)

# Extractor that only runs when an SSN annotation already exists
client.settings_profiles.set_extraction_workflow(
    profile_id=50217,
    enabled=True,
    steps=[
        WorkflowStep(
            extractor_id=594,
            condition=[
                JsonSearchQueryItem(
                    parameter="annotators",
                    value="annotation.16",
                    type="text",
                    match_strategy="exists",
                )
            ],
        )
    ],
)

# Disable extraction
client.settings_profiles.set_extraction_workflow(
    profile_id=50217,
    enabled=False,
)
```

---

### Searching the Index

```python
from dxrpy.index.json_search_query import JsonSearchQuery, JsonSearchQueryItem

query = JsonSearchQuery(
    datasource_ids=["123"],
    query_items=[
        JsonSearchQueryItem(parameter="match_all", value={}, type="match")
    ],
)
results = client.index.search(query)

print(f"Total hits: {results.total_hits}")
for hit in results.hits:
    print(hit.file_name, hit.labels)
```

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md).
