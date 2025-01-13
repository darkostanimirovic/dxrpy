import pytest
from unittest.mock import patch, MagicMock
from dxrpy.index.index import Index
from dxrpy.index.search_results import SearchResult
from dxrpy.index.json_search_query import JsonSearchQuery, JsonSearchQueryItem


@pytest.fixture
def query():
    # Correct instantiation of JsonSearchQuery with query items
    query_item = JsonSearchQueryItem(parameter="match_all", value={}, type="match")
    return JsonSearchQuery(query_items=[query_item])


@pytest.fixture
def search_result_data():
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


@patch("dxrpy.dxr_client.DXRHttpClient.get_instance")
def test_search(mock_get_instance, query, search_result_data):
    mock_client = MagicMock()
    mock_client.post.return_value = search_result_data
    mock_get_instance.return_value = mock_client

    index = Index()
    result = index.search(query)

    assert isinstance(result, SearchResult)
    assert result.total_hits == 1
    assert result.max_score == 1.0
    assert result.took == 1
    assert not result.timed_out
    assert len(result.hits) == 1
    assert result.hits[0].file_name == "test_file.py"
