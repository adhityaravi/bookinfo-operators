"""Unit tests for ratings charm."""

import unittest
from unittest.mock import MagicMock, patch

import ops.testing
from charm import RatingsK8sCharm


class TestRatingsCharm(unittest.TestCase):
    """Test cases for RatingsK8sCharm."""

    def setUp(self):
        """Set up test fixtures."""
        self.harness = ops.testing.Harness(RatingsK8sCharm)
        self.addCleanup(self.harness.cleanup)
        self.harness.begin()

    def test_charm_initializes(self):
        """Test that charm initializes without errors."""
        self.assertIsInstance(self.harness.charm, RatingsK8sCharm)

    def test_pebble_ready_sets_status(self):
        """Test that pebble ready event sets appropriate status."""
        self.harness.container_pebble_ready("bookinfo-ratings")
        self.assertIsInstance(
            self.harness.model.unit.status, (ops.WaitingStatus, ops.ActiveStatus, ops.MaintenanceStatus)
        )