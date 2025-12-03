"""
Global pytest configuration and fixtures for ExportReady.AI
"""

import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    """Return an API test client."""
    return APIClient()


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """Enable database access for all tests by default."""
    pass

