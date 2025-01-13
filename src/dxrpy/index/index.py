import json

from dxrpy.dxr_client import DXRHttpClient
from .json_search_query import JsonSearchQuery
from .search_results import SearchResult


class Index:
    """
    Index is responsible for managing the indexing of data.

    Attributes:
        client (DXRClient): The DXR client instance.
    """

    def search(self, query: JsonSearchQuery) -> SearchResult:
        """
        Searches the index with the given query.

        Args:
            query (JsonSearchQuery): The query to search for.

        Returns:
            SearchResult: The result of the search.
        """
        url = f"/indexed-files/search"
        payload = json.dumps(query.to_dict())
        results = DXRHttpClient.get_instance().post(url, data=payload)

        return SearchResult(results)
