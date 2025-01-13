from typing import List, Optional


class Annotation:
    def __init__(self, value: str, start: int, end: int):
        self.value = value
        self.start = start
        self.end = end


class Annotator:
    def __init__(self, id: int):
        self.id = id
        self.annotations: List[Annotation] = []
        self._unique_count: Optional[int] = None

    def add_annotation(self, annotation: Annotation):
        self.annotations.append(annotation)
        self._unique_count = None  # Invalidate cache

    @property
    def unique_count(self) -> int:
        if self._unique_count is None:
            unique_annotations = {annotation.value for annotation in self.annotations}
            self._unique_count = len(unique_annotations)
        return self._unique_count
