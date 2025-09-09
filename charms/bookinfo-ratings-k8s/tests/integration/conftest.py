"""Fixtures for ratings charm integration tests."""

import pytest
from pytest_jubilant import pack, get_resources


@pytest.fixture(scope="module")
def charm():
    """Build and package the ratings charm."""
    return pack(".")


@pytest.fixture(scope="module")
def resources():
    """Get resources for ratings charm."""
    return get_resources(".")