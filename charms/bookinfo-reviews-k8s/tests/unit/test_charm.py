"""Unit tests for reviews charm."""

import unittest

import ops.testing

from charm import ReviewsK8sCharm


class TestReviewsCharm(unittest.TestCase):
    """Test cases for ReviewsK8sCharm."""

    def setUp(self):
        """Set up test fixtures."""
        self.harness = ops.testing.Harness(ReviewsK8sCharm)
        self.addCleanup(self.harness.cleanup)
        self.harness.begin()

    def test_charm_initializes(self):
        """Test that charm initializes without errors."""
        self.assertIsInstance(self.harness.charm, ReviewsK8sCharm)

    def test_pebble_ready_sets_status(self):
        """Test that pebble ready event sets appropriate status."""
        self.harness.container_pebble_ready("bookinfo-reviews")
        self.assertIsInstance(
            self.harness.model.unit.status,
            (ops.WaitingStatus, ops.ActiveStatus, ops.MaintenanceStatus),
        )
