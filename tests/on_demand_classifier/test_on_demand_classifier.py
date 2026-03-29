import time

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, call

from dxrpy.on_demand_classifier.on_demand_classifier import (
    OnDemandClassifier,
    RunJobResult,
)
from dxrpy.on_demand_classifier.job import OnDemandClassifierJob
from dxrpy.utils.file_utils import File


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _job_data(
    job_id="job-1", state="QUEUED", datasource_scan_id=42, datasource_id=7,
):
    return {
        "id": job_id,
        "datasourceId": datasource_id,
        "datasourceScanId": datasource_scan_id,
        "state": state,
        "timeToLive": 3600,
        "submittedAt": "2026-03-01T00:00:00Z",
    }


def _search_response(hits=None):
    """Minimal Index.search() SearchResult mock data."""
    raw_hits = hits or []
    return MagicMock(hits=raw_hits)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_client():
    with patch("dxrpy.dxr_client.DXRHttpClient.get_instance") as mock_get:
        client = MagicMock()
        mock_get.return_value = client
        yield client


@pytest.fixture
def odc(mock_client):
    return OnDemandClassifier()


# ---------------------------------------------------------------------------
# OnDemandClassifier.create
# ---------------------------------------------------------------------------

class TestCreate:
    def test_create_posts_files(self, odc, mock_client):
        mock_client.post.return_value = _job_data()
        f = File(b"file-content")
        job = odc.create([f], datasource_id=7)
        assert job.id == "job-1"
        mock_client.post.assert_called_once()
        url = mock_client.post.call_args.args[0]
        assert "/on-demand-classifiers/7/jobs" in url

    def test_create_returns_job(self, odc, mock_client):
        mock_client.post.return_value = _job_data(state="QUEUED")
        job = odc.create([File(b"data")], datasource_id=5)
        assert isinstance(job, OnDemandClassifierJob)
        assert job.state == "QUEUED"


# ---------------------------------------------------------------------------
# OnDemandClassifier.get
# ---------------------------------------------------------------------------

class TestGet:
    def test_get_job(self, odc, mock_client):
        mock_client.get.return_value = _job_data(state="FINISHED")
        job = odc.get("job-1", datasource_id=7)
        assert job.finished()
        mock_client.get.assert_called_once_with(
            "/on-demand-classifiers/7/jobs/job-1"
        )


# ---------------------------------------------------------------------------
# OnDemandClassifier.select_available_datasource
# ---------------------------------------------------------------------------

class TestSelectAvailableDatasource:
    def test_single_datasource(self, odc):
        assert odc.select_available_datasource([42]) == 42

    @patch("dxrpy.on_demand_classifier.on_demand_classifier.DatasourceIngester")
    def test_skips_crawling_datasource(self, MockIngester, odc):
        # First datasource is crawling, second is idle
        mock_status_crawling = {"items": [{"crawl_active": True}]}
        mock_status_idle = {"items": [{"crawl_active": False}]}

        ingester_instances = []
        def make_ingester(ds_id):
            m = MagicMock()
            if ds_id == 1:
                m.index_status.return_value = mock_status_crawling
            else:
                m.index_status.return_value = mock_status_idle
            ingester_instances.append(m)
            return m

        MockIngester.side_effect = make_ingester

        # Force deterministic order by patching shuffle to no-op
        with patch("dxrpy.on_demand_classifier.on_demand_classifier.random.shuffle"):
            result = odc.select_available_datasource([1, 2])
        assert result == 2


# ---------------------------------------------------------------------------
# RunJobResult
# ---------------------------------------------------------------------------

class TestRunJobResult:
    def test_fields(self):
        job = OnDemandClassifierJob(_job_data())
        r = RunJobResult(hits=[], job=job, scan_id=42)
        assert r.hits == []
        assert r.scan_id == 42
        assert r.job is job

    def test_scan_id_optional(self):
        job = OnDemandClassifierJob(_job_data())
        r = RunJobResult(hits=[], job=job)
        assert r.scan_id is None


# ---------------------------------------------------------------------------
# OnDemandClassifier.run_job
# ---------------------------------------------------------------------------

class TestRunJob:
    def _setup_run_job(self, mock_client, states=None, scan_id=42, hits=None):
        """Wire up mock_client to simulate a job lifecycle."""
        states = states or ["QUEUED", "PROCESSING", "FINISHED"]
        state_iter = iter(states)

        # create() returns initial job
        mock_client.post.return_value = _job_data(state=states[0], datasource_scan_id=scan_id)

        # get() cycles through states
        def get_side_effect(url):
            try:
                state = next(state_iter)
            except StopIteration:
                state = states[-1]
            return _job_data(state=state, datasource_scan_id=scan_id)

        mock_client.get.side_effect = get_side_effect

        return hits or []

    @patch("dxrpy.on_demand_classifier.on_demand_classifier.Index")
    @patch("dxrpy.on_demand_classifier.on_demand_classifier.time.sleep")
    def test_run_job_basic(self, mock_sleep, MockIndex, odc, mock_client):
        self._setup_run_job(mock_client, states=["QUEUED", "FINISHED"])
        mock_hit = MagicMock()
        MockIndex.return_value.search.return_value = _search_response([mock_hit])

        result = odc.run_job([File(b"data")], [7], sleep=0)

        assert isinstance(result, RunJobResult)
        assert len(result.hits) == 1
        assert result.scan_id == 42

    @patch("dxrpy.on_demand_classifier.on_demand_classifier.Index")
    @patch("dxrpy.on_demand_classifier.on_demand_classifier.time.sleep")
    def test_run_job_wraps_mixed_inputs(self, mock_sleep, MockIndex, odc, mock_client):
        """str, Path, and File inputs are all accepted."""
        self._setup_run_job(mock_client, states=["FINISHED"])
        MockIndex.return_value.search.return_value = _search_response([])

        # bytes-backed File objects don't need real files on disk
        result = odc.run_job(
            [File(b"data1"), File(b"data2")],
            [7],
            sleep=0,
        )
        assert isinstance(result, RunJobResult)

    def test_file_wrapping_logic(self, odc, mock_client):
        """Verify that raw str/Path values become File objects."""
        from dxrpy.on_demand_classifier.on_demand_classifier import File as ODCFile
        inputs = ["/tmp/a.txt", Path("/tmp/b.txt"), File(b"raw")]
        wrapped = [f if isinstance(f, ODCFile) else ODCFile(f) for f in inputs]
        assert all(isinstance(w, ODCFile) for w in wrapped)
        assert isinstance(wrapped[0].file, str)
        assert isinstance(wrapped[1].file, Path)
        assert isinstance(wrapped[2].file, bytes)

    @patch("dxrpy.on_demand_classifier.on_demand_classifier.Index")
    @patch("dxrpy.on_demand_classifier.on_demand_classifier.time.sleep")
    def test_run_job_raises_on_failure(self, mock_sleep, MockIndex, odc, mock_client):
        self._setup_run_job(mock_client, states=["QUEUED", "FAILED"])

        with pytest.raises(RuntimeError, match="ODC job .* failed"):
            odc.run_job([File(b"data")], [7], sleep=0)

    @patch("dxrpy.on_demand_classifier.on_demand_classifier.Index")
    @patch("dxrpy.on_demand_classifier.on_demand_classifier.time.time")
    @patch("dxrpy.on_demand_classifier.on_demand_classifier.time.sleep")
    def test_run_job_timeout(self, mock_sleep, mock_time, MockIndex, odc, mock_client):
        # Job stays in PROCESSING, never finishes
        mock_client.post.return_value = _job_data(state="PROCESSING")
        mock_client.get.return_value = _job_data(state="PROCESSING")

        # Simulate time passing: first call sets deadline, subsequent exceed it
        mock_time.side_effect = [100.0, 200.0, 300.0]

        with pytest.raises(TimeoutError, match="timed out after 10s"):
            odc.run_job([File(b"data")], [7], sleep=0, timeout=10)

    @patch("dxrpy.on_demand_classifier.on_demand_classifier.Index")
    @patch("dxrpy.on_demand_classifier.on_demand_classifier.time.sleep")
    def test_run_job_custom_page_size(self, mock_sleep, MockIndex, odc, mock_client):
        self._setup_run_job(mock_client, states=["FINISHED"])
        MockIndex.return_value.search.return_value = _search_response([])

        odc.run_job([File(b"data")], [7], sleep=0, page_size=50)

        # Verify the search query used the custom page_size
        search_call = MockIndex.return_value.search.call_args
        query = search_call.args[0]
        assert query.page_size == 50

    @patch("dxrpy.on_demand_classifier.on_demand_classifier.Index")
    @patch("dxrpy.on_demand_classifier.on_demand_classifier.time.sleep")
    def test_run_job_no_timeout(self, mock_sleep, MockIndex, odc, mock_client):
        """With timeout=None, no deadline is set (default behaviour)."""
        self._setup_run_job(mock_client, states=["QUEUED", "QUEUED", "FINISHED"])
        MockIndex.return_value.search.return_value = _search_response([])

        result = odc.run_job([File(b"data")], [7], sleep=0, timeout=None)
        assert isinstance(result, RunJobResult)
