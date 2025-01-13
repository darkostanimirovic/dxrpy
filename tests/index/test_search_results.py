import pytest
from unittest.mock import patch, MagicMock

from dxrpy.index.search_results import Hit, SearchResult


@pytest.fixture
def hit_data():
    return {
        "_index": "test_index",
        "_id": "1",
        "_score": 1.0,
        "_source": {
            "ds#file_name": "test_file.py",
            "dxr#tags": [1, 2],
            "annotations": "[test, 0, 4, 1]",
            "ai#category": "test_category",
        },
    }


@pytest.fixture
def hit(hit_data):
    with patch("dxrpy.DXRHttpClient.get_instance") as mock_get_instance:
        mock_client = MagicMock()
        mock_get_instance.return_value = mock_client
        yield Hit(hit_data)


@pytest.fixture
def result_data():
    return {
        "_shards": {},
        "hits": {
            "total": {"value": 1},
            "max_score": 1.0,
            "hits": [
                {
                    "_index": "test_index",
                    "_id": "1",
                    "_score": 1.0,
                    "_source": {
                        "ds#file_name": "test_file.py",
                        "dxr#tags": [1, 2],
                        "annotations": "[test, 0, 4, 1]",
                        "ai#category": "test_category",
                    },
                }
            ],
        },
        "took": 1,
        "timed_out": False,
    }


@pytest.fixture
def search_result(result_data):
    with patch("dxrpy.dxr_client.DXRHttpClient.get_instance") as mock_get_instance:
        mock_client = MagicMock()
        mock_get_instance.return_value = mock_client
        yield SearchResult(result_data)


def test_metadata(hit, hit_data):
    assert hit.metadata == hit_data["_source"]


def test_file_name(hit):
    assert hit.file_name == "test_file.py"


@patch("dxrpy.index.search_results.Hit._fetch_label")
def test_labels(mock_fetch_label, hit):
    mock_fetch_label.return_value = {
        "id": 1,
        "name": "test_label",
        "description": "test_description",
        "hexColor": "#FFFFFF",
        "type": "test_type",
    }
    labels = hit.labels
    assert len(labels) == 2
    assert labels[0].name == "test_label"


def test_annotators(hit):
    annotators = hit.annotators
    assert len(annotators) == 1
    assert annotators[0].annotations[0].value == "test"


def test_category(hit):
    assert hit.category == "test_category"


def test_hits(search_result):
    assert len(search_result.hits) == 1
    assert isinstance(search_result.hits[0], Hit)


def test_total_hits(search_result):
    assert search_result.total_hits == 1


def test_max_score(search_result):
    assert search_result.max_score == 1.0


def test_took(search_result):
    assert search_result.took == 1


def test_timed_out(search_result):
    assert not search_result.timed_out
