import time
import logging
import random

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Union

from dxrpy.dxr_client import DXRHttpClient
from ..datasource.ingester.datasource_ingester import DatasourceIngester

from ..index import Index, JsonSearchQuery, JsonSearchQueryItem, Hit

from .job import OnDemandClassifierJob
from ..utils.file_utils import File

logger = logging.getLogger(__name__)


@dataclass
class RunJobResult:
    """Result of an :meth:`OnDemandClassifier.run_job` call.

    Carries the hits *and* the job metadata so callers can correlate
    results with a specific scan.
    """

    hits: List[Hit]
    job: OnDemandClassifierJob
    scan_id: Optional[int] = None


class OnDemandClassifier:
    """
    OnDemandClassifier is responsible for running classification jobs on demand.

    Attributes:
        client (DXRClient): The DXR client instance.
    """

    def __init__(self):
        """
        Initializes the OnDemandClassifier with the DXR client singleton.
        """
        self.client: DXRHttpClient = DXRHttpClient.get_instance()

    def create(self, files: List[File], datasource_id: int) -> OnDemandClassifierJob:
        """
        Creates a classification job with files from various sources.

        Args:
            files: List of File objects.
            datasource_id: The data source ID

        Returns:
            OnDemandClassifierJob: The created classification job.
        """
        upload_files = [file.to_tuple() for file in files]

        response = self.client.post(
            f"/on-demand-classifiers/{datasource_id}/jobs", files=upload_files
        )
        return OnDemandClassifierJob(response)

    def get(self, job_id: str, datasource_id: int) -> OnDemandClassifierJob:
        """
        Retrieves the status of a classification job by job ID and data source ID.

        Args:
            job_id (str): The ID of the job.
            datasource_id (int): The ID of the data source.

        Returns:
            OnDemandClassifierJob: The classification job with the given ID.
        """
        response = self.client.get(
            f"/on-demand-classifiers/{datasource_id}/jobs/{job_id}"
        )
        return OnDemandClassifierJob(response)

    def select_available_datasource(self, datasource_ids: List[int]) -> int:
        """
        Selects a datasource that is not being crawled at the moment.

        Args:
            datasource_ids (List[int]): A list of data source IDs.

        Returns:
            int: The selected data source ID.
        """
        if len(datasource_ids) == 1:
            return datasource_ids[0]

        random.shuffle(datasource_ids)
        for datasource_id in datasource_ids:
            ingester = DatasourceIngester(datasource_id)
            status = ingester.index_status()
            if not status["items"] or not status["items"][0]["crawl_active"]:
                return datasource_id
        return datasource_ids[-1]

    def run_job(
        self,
        files: List[Union[File, str, Path]],
        datasource_ids: List[int],
        sleep: int = 1,
        timeout: Optional[int] = None,
        page_size: int = 100,
    ) -> RunJobResult:
        """
        Submit files for classification, wait for completion, and return results.

        This is the primary high-level method for running ODC jobs.  It
        handles datasource selection, job submission, polling, and result
        retrieval in a single call.

        Args:
            files: Files to classify. Accepts :class:`File` objects, file
                paths (``str`` or ``Path``), or a mix.
            datasource_ids: One or more datasource IDs to submit to.
                When multiple are provided, an available (non-crawling)
                datasource is selected automatically.
            sleep: Seconds between poll requests (default 1).
            timeout: Maximum seconds to wait for the job to finish.
                ``None`` means wait indefinitely (original behaviour).
            page_size: Number of hits to request per search page
                (default 100).

        Returns:
            RunJobResult: Contains the list of :class:`Hit` objects, the
                finished :class:`OnDemandClassifierJob`, and the
                ``scan_id``.

        Raises:
            RuntimeError: If the job enters the ``FAILED`` state.
            TimeoutError: If *timeout* is set and the job does not finish
                in time.
        """
        wrapped_files = [
            f if isinstance(f, File) else File(f) for f in files
        ]

        selected_datasource_id = self.select_available_datasource(datasource_ids)

        job = self.create(wrapped_files, selected_datasource_id)
        deadline = (time.time() + timeout) if timeout is not None else None
        last_state = ""

        while True:
            job = self.get(job.id, selected_datasource_id)
            state = job.state or ""

            if state != last_state:
                logger.info("Job %s → %s", job.id, state)
                last_state = state
            else:
                logger.debug("Job %s state: %s", job.id, state)

            if job.finished():
                break
            if job.failed():
                raise RuntimeError(f"ODC job {job.id} failed")

            if deadline is not None and time.time() >= deadline:
                raise TimeoutError(
                    f"ODC job {job.id} timed out after {timeout}s "
                    f"(last state: {last_state})"
                )

            time.sleep(sleep)

        # Ensure smart labels are applied by waiting a bit more
        time.sleep(0.3)

        scan_id = job.datasource_scan_id

        # Get metadata for all files in this scan
        query = JsonSearchQuery(
            page_size=page_size,
            query_items=[
                JsonSearchQueryItem(
                    parameter="dxr#datasource_scan_id",
                    value=scan_id,
                    type="number",
                )
            ]
        )
        search_result = Index().search(query)

        return RunJobResult(
            hits=search_result.hits,
            job=job,
            scan_id=scan_id,
        )
