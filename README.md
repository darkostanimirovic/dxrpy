# Data X-Ray Python Library

Unofficial Python library for the Data X-Ray API.

> **Warning**
> This library is unofficial and unsupported and may change at any time. Not for production use.

## Installation

To install the library, use pip:

```sh
pip install dxrpy
```

## Usage

### Initializing the Client

To interact with the DXR API, you need to initialize the DXRClient with your API URL and API key.

Parameters:

- `base_url` (str): The base URL for the DXR API.
- `api_key` (str): The API key for authenticating with the DXR API.
- `ignore_ssl` (bool): Whether to ignore SSL certificate verification.

```python
from dxrpy import DXRClient

api_url = "https://api.example.com"
api_key = "your_api_key"

client = DXRClient(api_url, api_key)
```

### On-Demand Classifier

The OnDemandClassifier allows you to create and manage classification jobs.

```python
from dxrpy.utils import File

# Select one or more files
files = [File("path/to/file1.txt"), File("path/to/file2.txt")]

# Target datasource. If you have more than one, the client
# will pick the first one that is not crawling at the moment.
datasource_ids = [123]

# Create a classification job
hits = client.on_demand_classifier.run_job(files, datasource_ids)

# Receive a list of Hit objects for each file
print(hit.labels for hit in hits)
```
