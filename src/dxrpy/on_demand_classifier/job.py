from typing import Any, Dict


class OnDemandClassifierJob:
    def __init__(self, job_data: Dict[str, Any]):
        self.id: str = job_data['id']
        self.datasource_id = job_data.get('datasourceId')
        self.datasource_scan_id = job_data.get('datasourceScanId')
        self.time_to_live = job_data.get('timeToLive')
        self.state = job_data.get('state')
        self.recrawl_dispatch_failures = job_data.get('recrawlDispatchFailures')
        self.submitted_at = job_data.get('submittedAt')
        self.submitted_by_user_id = job_data.get('submittedByUserId')
        self.organizational_unit_id = job_data.get('organizationalUnitId')

    def finished(self) -> bool:
        return self.state == "FINISHED"

    def failed(self) -> bool:
        return self.state == "FAILED"
