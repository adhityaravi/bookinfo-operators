"""Fixtures for Bookinfo integration tests."""

import logging
import os
from typing import Dict

import jubilant
import pytest

logger = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def bookinfo_juju():
    """Create a Juju model for bookinfo deployment."""
    keep_models: bool = os.environ.get("KEEP_MODELS") is not None
    with jubilant.temp_model(keep=keep_models) as juju:
        yield juju


@pytest.fixture(scope="module")
def istio_system_juju():
    """Create a Juju model for istio-system deployment."""
    keep_models: bool = os.environ.get("KEEP_MODELS") is not None
    with jubilant.temp_model(keep=keep_models) as juju:
        yield juju


@pytest.fixture
def juju_run_output() -> Dict:
    """Store the output from juju run actions."""
    return {}
