import time
import logging

from typing import List

from dxrpy.dxr_client import DXRHttpClient
from ..datasource.ingester.datasource_ingester import DatasourceIngester

from ..index import Index, JsonSearchQuery, JsonSearchQueryItem, Hit

from .job import OnDemandClassifierJob
from ..utils.file_utils import File

logger = logging.getLogger(__name__)


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

        for datasource_id in datasource_ids:
            ingester = DatasourceIngester(datasource_id)
            status = ingester.index_status()
            if not status["items"][0]["crawl_active"]:
                return datasource_id
        return datasource_ids[-1]

    def run_job(
        self, files: List[File], datasource_ids: List[int], sleep: int = 1
    ) -> List[Hit]:
        """
        Runs a classification job with the given files and data source ID.

        Args:
            files (List[File]): A list of File objects to process.
            datasource_ids (List[int]): A list of data source IDs.
            sleep (int): The sleep interval between job status checks.

        Returns:
            List[Hit]: A list of hits from the job.
        """
        selected_datasource_id = self.select_available_datasource(datasource_ids)

        job = self.create(files, selected_datasource_id)
        while True:
            job = self.get(job.id, selected_datasource_id)
            logger.debug(f"[{job.id}] Status: {job.state}")

            if job.finished():
                logger.debug(f"Job {job.id} finished")
                break
            elif job.failed():
                logger.debug(f"Job {job.id} failed")
                return []

            time.sleep(sleep)

        # Ensure smart labels are applied by waiting a bit more
        time.sleep(0.3)

        # Get metadata for all files in this scan
        query = JsonSearchQuery(
            query_items=[
                JsonSearchQueryItem(
                    parameter="dxr#datasource_scan_id",
                    value=job.datasource_scan_id,
                    type="number",
                )
            ]
        )
        search_result = Index().search(query)
        return search_result.hits
