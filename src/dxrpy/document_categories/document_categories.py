from typing import Any, Dict, List
from dxrpy.dxr_client import DXRHttpClient

class DocumentCategory:
    def __init__(self, data: Dict[str, Any]):
        self.id = data.get('id')
        self.name = data.get('name')
        self.description = data.get('description')

class DocumentCategories:
    def __init__(self):
        self.client: DXRHttpClient = DXRHttpClient.get_instance()

    def get_all(self) -> List[DocumentCategory]:
        response = self.client.get("/api/document-categories")
        return [DocumentCategory(data) for data in response]

    def create(self, category_data: Dict[str, Any]) -> DocumentCategory:
        response = self.client.post("/api/document-categories", json=category_data)
        return DocumentCategory(response)

    def update(self, category_data: Dict[str, Any]) -> DocumentCategory:
        response = self.client.put("/api/document-categories", json=category_data)
        return DocumentCategory(response)

    def replace_all(self, categories_data: List[Dict[str, Any]]) -> None:
        self.client.post("/api/document-categories/replace-all", json=categories_data)

    def delete(self, category_id: int) -> None:
        self.client.delete(f"/api/document-categories/{category_id}")
