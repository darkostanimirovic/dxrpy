"""Tests for DXRHttpClient URL normalisation."""

import pytest
from dxrpy.dxr_client import DXRHttpClient


class TestApiUrlNormalization:
    """The client must guarantee that api_url always ends with /api."""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        DXRHttpClient._instance = None
        yield
        DXRHttpClient._instance = None

    def test_bare_host(self):
        client = DXRHttpClient("https://example.com", "key")
        assert client.api_url == "https://example.com/api"

    def test_host_with_trailing_slash(self):
        client = DXRHttpClient("https://example.com/", "key")
        assert client.api_url == "https://example.com/api"

    def test_host_with_api(self):
        client = DXRHttpClient("https://example.com/api", "key")
        assert client.api_url == "https://example.com/api"

    def test_host_with_api_trailing_slash(self):
        client = DXRHttpClient("https://example.com/api/", "key")
        assert client.api_url == "https://example.com/api"
