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


# ---------------------------------------------------------------------------
# Hit.tag_ids
# ---------------------------------------------------------------------------

def test_tag_ids(hit):
    assert hit.tag_ids == [1, 2]


def test_tag_ids_empty():
    """Hit with no tags returns an empty list."""
    data = {"_source": {"annotations": ""}}
    hit = Hit(data)
    assert hit.tag_ids == []


# ---------------------------------------------------------------------------
# Hit.annotator_ids
# ---------------------------------------------------------------------------

def test_annotator_ids(hit):
    assert hit.annotator_ids() == {1}


def test_annotator_ids_multiple():
    data = {
        "_source": {
            "annotations": "[foo, 0, 3, 5][bar, 4, 7, 10][baz, 8, 11, 5]",
        },
    }
    hit = Hit(data)
    assert hit.annotator_ids() == {5, 10}


def test_annotator_ids_empty():
    data = {"_source": {"annotations": ""}}
    hit = Hit(data)
    assert hit.annotator_ids() == set()


# ---------------------------------------------------------------------------
# Hit.to_dict / from_dict round-trip
# ---------------------------------------------------------------------------

def test_to_dict(hit):
    d = hit.to_dict()
    assert d["file_name"] == "test_file.py"
    assert d["category"] == "test_category"
    assert d["tag_ids"] == [1, 2]
    assert len(d["annotations"]) == 1
    ann = d["annotations"][0]
    assert ann["annotator_id"] == 1
    assert ann["value"] == "test"
    assert ann["start"] == 0
    assert ann["end"] == 4


def test_from_dict_round_trip(hit):
    """to_dict → from_dict preserves all observable properties."""
    d = hit.to_dict()
    restored = Hit.from_dict(d)
    assert restored.file_name == hit.file_name
    assert restored.category == hit.category
    assert restored.tag_ids == hit.tag_ids
    assert restored.annotator_ids() == hit.annotator_ids()


def test_from_dict_multiple_annotations():
    data = {
        "file_name": "doc.txt",
        "category": "financial",
        "tag_ids": [7],
        "annotations": [
            {"annotator_id": 3, "value": "555-1234", "start": 0, "end": 8},
            {"annotator_id": 16, "value": "123 Main St", "start": 10, "end": 21},
        ],
    }
    hit = Hit.from_dict(data)
    assert hit.file_name == "doc.txt"
    assert hit.category == "financial"
    assert hit.tag_ids == [7]
    assert hit.annotator_ids() == {3, 16}
    assert len(hit.annotators) == 2


def test_from_dict_empty():
    """from_dict with minimal/empty data doesn't crash."""
    hit = Hit.from_dict({})
    assert hit.file_name == ""
    assert hit.category == ""
    assert hit.tag_ids == []
    assert hit.annotator_ids() == set()


def test_from_dict_no_client_required():
    """from_dict works without DXRHttpClient initialised."""
    hit = Hit.from_dict({"file_name": "x.txt", "annotations": []})
    assert hit.file_name == "x.txt"
    assert hit.client is None


def test_from_dict_labels_raises_without_client():
    """Accessing labels on an offline hit raises RuntimeError."""
    hit = Hit.from_dict({"tag_ids": [99]})
    with pytest.raises(RuntimeError, match="DXRHttpClient is not initialised"):
        _ = hit.labels
