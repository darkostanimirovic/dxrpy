import re
from typing import Any, Dict, List

from dxrpy.dxr_client import DXRHttpClient

from .annotators import Annotation, Annotator

from .labels import Label


class Hit:
    def __init__(self, hit_data: Dict[str, Any]):
        self.index = hit_data.get("_index")
        self.id = hit_data.get("_id")
        self.score = hit_data.get("_score")
        self._metadata = hit_data.get("_source", {})

        self.client = DXRHttpClient.get_instance()
        self._labels_cache: Dict[int, Label] = {}

    def _fetch_label(self, tag_id: int) -> Dict[str, Any]:
        url = f"/tags/{tag_id}"
        return self.client.get(url)

    def _extract_annotators(self) -> Dict[int, Annotator]:
        annotators: dict[int, Annotator] = {}
        annotations_str = self.metadata.get("annotations", "")
        annotation_pattern = re.compile(r"\[([^,]+), (\d+), (\d+), (\d+)\]")
        for match in annotation_pattern.finditer(annotations_str):
            value, start, end, id = match.groups()
            id = int(id)
            if id not in annotators:
                annotators[id] = Annotator(id)
            annotators[id].add_annotation(Annotation(value, int(start), int(end)))
        return annotators

    @property
    def metadata(self) -> Dict[str, Any]:
        return self._metadata

    @property
    def file_name(self) -> str:
        return self.metadata.get("ds#file_name", "")

    @property
    def labels(self) -> List[Label]:
        tag_ids = self.metadata.get("dxr#tags", [])
        labels = []
        for tag_id in tag_ids:
            if tag_id not in self._labels_cache:
                label_data = self._fetch_label(tag_id)
                self._labels_cache[tag_id] = Label.from_dict(label_data)
            labels.append(self._labels_cache[tag_id])
        return labels

    @property
    def annotators(self) -> List[Annotator]:
        return list(self._extract_annotators().values())

    @property
    def category(self) -> str:
        return self.metadata.get("ai#category", "")


class SearchResult:
    def __init__(self, result_data: Dict[str, Any]):
        self.shards = result_data["_shards"]
        self.total_hits = result_data["hits"]["total"]["value"]
        self.max_score = result_data["hits"]["max_score"]
        self._hits = [Hit(hit) for hit in result_data["hits"]["hits"]]
        self.took = result_data["took"]
        self.timed_out = result_data["timed_out"]

    @property
    def hits(self) -> List[Hit]:
        return self._hits
