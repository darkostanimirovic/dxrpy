from typing import List
import requests


class DXRHttpClient:
    """
    A singleton HTTP client for interacting with the DXR API.
    """

    _instance = None

    def __init__(self, api_url: str, api_key: str, ignore_ssl: bool = False):
        """
        Initialize the DXRHttpClient with the given API URL, API key, and SSL verification option.

        :param api_url: The base URL of the DXR API.
        :param api_key: The API key for authentication.
        :param ignore_ssl: Whether to ignore SSL certificate verification.
        """
        self.api_url = api_url
        self.api_key = api_key
        self.ignore_ssl = ignore_ssl
        self.session = requests.Session()
        self.session.headers.update(
            {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        )

    @classmethod
    def get_instance(
        cls,
        api_url: str | None = None,
        api_key: str | None = None,
        ignore_ssl: bool = False,
    ) -> "DXRHttpClient":
        """
        Get the singleton instance of the DXRHttpClient. If it does not exist, create it.

        :param api_url: The base URL of the DXR API (required for first initialization).
        :param api_key: The API key for authentication (required for first initialization).
        :param ignore_ssl: Whether to ignore SSL certificate verification.
        :return: The singleton instance of DXRHttpClient.
        :raises ValueError: If the instance is not initialized and API URL or API key is not provided.
        """
        if cls._instance is None:
            if not api_url or not api_key:
                raise ValueError(
                    "API URL and API key must be provided for the first initialization."
                )
            cls._instance = cls(api_url, api_key, ignore_ssl)
        return cls._instance

    def request(self, method: str, endpoint: str, **kwargs) -> dict:
        """
        Make an HTTP request to the DXR API.

        :param method: The HTTP method (e.g., 'GET', 'POST').
        :param endpoint: The API endpoint to call.
        :param kwargs: Additional arguments to pass to the request.
        :return: The JSON response from the API.
        :raises requests.exceptions.HTTPError: If the HTTP request returned an unsuccessful status code.
        """
        if not self.api_url.endswith("/"):
            self.api_url += "/"
        if endpoint.startswith("/"):
            endpoint = endpoint[1:]

        url = f"{self.api_url}{endpoint}"
        response = self.session.request(
            method, url, verify=not self.ignore_ssl, **kwargs
        )
        response.raise_for_status()
        return response.json()

    def put(self, url: str, **kwargs) -> dict:
        """
        Make a PUT request to the DXR API.

        :param url: The API endpoint to call.
        :param kwargs: Additional arguments to pass to the request.
        :return: The JSON response from the API.
        """
        return self.request("PUT", url, **kwargs)

    def delete(self, url: str, **kwargs) -> None:
        """
        Make a DELETE request to the DXR API.

        :param url: The API endpoint to call.
        :param kwargs: Additional arguments to pass to the request.
        """
        self.request("DELETE", url, **kwargs)

    def update_headers(self, headers: dict) -> None:
        """
        Update the headers for the HTTP session.

        :param headers: A dictionary of headers to update.
        """
        self.session.headers.update(headers)

    def get(self, url: str, **kwargs) -> dict:
        """
        Make a GET request to the DXR API.

        :param url: The API endpoint to call.
        :param kwargs: Additional arguments to pass to the request.
        :return: The JSON response from the API.
        """
        return self.request("GET", url, **kwargs)

    def post(self, url: str, files: List[tuple] | None = None, **kwargs) -> dict:
        """
        Make a POST request to the DXR API.

        :param url: The API endpoint to call.
        :param files: Files to include in the POST request.
        :param kwargs: Additional arguments to pass to the request.
        :return: The JSON response from the API.
        """
        self.session.headers["Content-Type"] = "application/json"

        if files:
            kwargs["files"] = files

            # Remove Content-Type header to allow 'multipart/form-data'
            if "Content-Type" in self.session.headers:
                del self.session.headers["Content-Type"]

        return self.request("POST", url, **kwargs)
