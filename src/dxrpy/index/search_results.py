import re
from typing import Any, Dict, List, Optional, Set

from dxrpy.dxr_client import DXRHttpClient

from .annotators import Annotation, Annotator

from .labels import Label


class Hit:
    """A single document hit from a DXR search or ODC scan."""

    def __init__(self, hit_data: Dict[str, Any], *, _client: Optional[DXRHttpClient] = None):
        self.index = hit_data.get("_index")
        self.id = hit_data.get("_id")
        self.score = hit_data.get("_score")
        self._metadata = hit_data.get("_source", {})
        self._client = _client
        self._labels_cache: Dict[int, Label] = {}

    @property
    def client(self) -> Optional[DXRHttpClient]:
        """Lazily resolve the HTTP client singleton.

        Returns ``None`` when the singleton has not been initialised
        (e.g. for offline/deserialized hits).
        """
        if self._client is None:
            try:
                self._client = DXRHttpClient.get_instance()
            except ValueError:
                pass
        return self._client

    @client.setter
    def client(self, value: Optional[DXRHttpClient]) -> None:
        self._client = value

    def _fetch_label(self, tag_id: int) -> Dict[str, Any]:
        if self.client is None:
            raise RuntimeError(
                "DXRHttpClient is not initialised; cannot fetch labels "
                "on an offline Hit."
            )
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
    def tag_ids(self) -> List[int]:
        """Smart-label tag IDs applied to this document."""
        return self.metadata.get("dxr#tags", [])

    @property
    def labels(self) -> List[Label]:
        labels = []
        for tag_id in self.tag_ids:
            if tag_id not in self._labels_cache:
                label_data = self._fetch_label(tag_id)
                self._labels_cache[tag_id] = Label.from_dict(label_data)
            labels.append(self._labels_cache[tag_id])
        return labels

    @property
    def annotators(self) -> List[Annotator]:
        return list(self._extract_annotators().values())

    def annotator_ids(self) -> Set[int]:
        """Return the set of unique annotator IDs found in this document."""
        return set(self._extract_annotators().keys())

    @property
    def category(self) -> str:
        return self.metadata.get("ai#category", "")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a JSON-safe dictionary.

        The output captures the document's file name, category, tag IDs,
        and flattened annotations — everything needed to reconstruct the
        hit for offline analysis without the original elasticsearch
        response.
        """
        annotations = []
        for annotator in self.annotators:
            for ann in annotator.annotations:
                annotations.append({
                    "annotator_id": annotator.id,
                    "value": ann.value,
                    "start": ann.start,
                    "end": ann.end,
                })
        return {
            "file_name": self.file_name,
            "category": self.category,
            "tag_ids": self.tag_ids,
            "annotations": annotations,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Hit":
        """Reconstruct a Hit from a dictionary produced by :meth:`to_dict`.

        The resulting Hit is a lightweight, offline object — the
        ``DXRHttpClient`` singleton does not need to be initialised.
        Label fetching will raise ``RuntimeError`` if the client is
        unavailable, but all other properties work normally.
        """
        ann_parts = []
        for a in data.get("annotations", []):
            ann_parts.append(
                f"[{a['value']}, {a['start']}, {a['end']}, {a['annotator_id']}]"
            )
        source = {
            "ds#file_name": data.get("file_name", ""),
            "ai#category": data.get("category", ""),
            "dxr#tags": data.get("tag_ids", []),
            "annotations": "".join(ann_parts),
        }
        return cls({"_source": source})


class SearchResult:
    def __init__(self, result_data: Dict[str, Any]):
        self.shards = result_data["_shards"]
        self.total_hits = result_data["hits"]["total"]["value"]
        self.max_score = result_data["hits"].get("max_score")
        self._hits = [Hit(hit) for hit in result_data["hits"]["hits"]]
        self.took = result_data["took"]
        self.timed_out = result_data["timed_out"]

    @property
    def hits(self) -> List[Hit]:
        return self._hits
