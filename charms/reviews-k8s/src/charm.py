#!/usr/bin/env python3

import logging
from typing import Dict, Optional

from ops.charm import CharmBase
from ops.framework import StoredState
from ops.main import main
from ops.model import ActiveStatus, BlockedStatus, MaintenanceStatus, WaitingStatus
from ops.pebble import LayerDict

from charms.bookinfo_lib.v0.bookinfo_service import BookinfoServiceProvider, BookinfoServiceConsumer

logger = logging.getLogger(__name__)

REVIEWS_PORT = 9080
SUPPORTED_VERSIONS = ["v1", "v2", "v3"]
VERSION_IMAGES = {
    "v1": "docker.io/istio/examples-bookinfo-reviews-v1:1.20.3",
    "v2": "docker.io/istio/examples-bookinfo-reviews-v2:1.20.3",
    "v3": "docker.io/istio/examples-bookinfo-reviews-v3:1.20.3",
}


class ReviewsK8sCharm(CharmBase):
    """Charm for the Reviews microservice."""

    _stored = StoredState()

    def __init__(self, *args):
        super().__init__(*args)
        self._stored.set_default(
            started=False,
            ratings_url=None
        )

        self.container = self.unit.get_container("reviews")

        self.framework.observe(self.on.reviews_pebble_ready, self._on_pebble_ready)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.on.update_status, self._on_update_status)

        # Provide reviews service endpoint
        self.service_provider = BookinfoServiceProvider(
            self,
            "reviews",
            9080
        )

        # Consume ratings service
        self.ratings_consumer = BookinfoServiceConsumer(self, "ratings")
        self.framework.observe(
            self.ratings_consumer.on.url_changed,
            self._on_ratings_url_changed
        )

    def _on_pebble_ready(self, event):
        """Handle the pebble ready event."""
        self._update_layer()
        self._stored.started = True
        self._update_status()

    def _on_config_changed(self, event):
        """Handle config changed event."""
        if not self._validate_config():
            self.unit.status = BlockedStatus(f"Invalid version: {self.config['version']}")
            return

        if not self._stored.started:
            event.defer()
            return

        self._update_layer()
        self._update_status()

    def _on_update_status(self, event):
        """Handle update status event."""
        self._update_status()

    def _on_ratings_url_changed(self, event):
        """Handle ratings URL changed."""
        self._stored.ratings_url = event.url
        if event.url:
            logger.info(f"Ratings service available at: {event.url}")
        else:
            logger.info("Ratings service unavailable")
        self._update_layer()
        self._update_status()

    def _validate_config(self) -> bool:
        """Validate configuration."""
        return self.config["version"] in SUPPORTED_VERSIONS

    def _update_status(self):
        """Update the charm status."""
        if not self._stored.started:
            self.unit.status = MaintenanceStatus("Waiting for pebble ready")
            return

        if not self.container.can_connect():
            self.unit.status = MaintenanceStatus("Waiting for container")
            return

        version = self.config["version"]
        if version in ["v2", "v3"] and not self._get_ratings_url():
            self.unit.status = WaitingStatus(f"Version {version} requires ratings service")
            return

        try:
            service = self.container.get_service("reviews")
            if service.is_running():
                self.unit.status = ActiveStatus(f"Running version {version}")
            else:
                self.unit.status = MaintenanceStatus("Service not running")
        except Exception as e:
            logger.error(f"Failed to check service status: {e}")
            self.unit.status = BlockedStatus("Failed to check service status")

    def _update_layer(self):
        """Update the Pebble layer configuration."""
        if not self.container.can_connect():
            logger.debug("Cannot connect to container")
            return

        layer = self._generate_layer()
        self.container.add_layer("reviews", layer, combine=True)
        
        try:
            self.container.replan()
            logger.info("Service layer updated")
        except Exception as e:
            logger.error(f"Failed to replan service: {e}")
            self.unit.status = BlockedStatus(f"Failed to start service: {e}")

    def _generate_layer(self) -> LayerDict:
        """Generate the Pebble layer configuration."""
        return {
            "summary": "Reviews service layer",
            "description": "Pebble layer for the Reviews microservice",
            "services": {
                "reviews": {
                    "override": "replace",
                    "summary": "Reviews service",
                    "command": "/opt/ol/wlp/bin/server run defaultServer",
                    "startup": "enabled",
                    "environment": self._get_environment(),
                }
            },
        }

    def _get_ratings_url(self) -> Optional[str]:
        """Get the ratings service URL."""
        return self._stored.ratings_url

    def _get_environment(self) -> Dict[str, str]:
        """Get environment variables for the service."""
        env = {
            "SERVICE_NAME": "reviews",
            "SERVICE_VERSION": self.config["version"],
            "LOG_DIR": "/tmp/logs",
            "SERVERDIRNAME": "reviews",
        }

        # Extract hostname and port from URL for upstream compatibility
        ratings_url = self._get_ratings_url()
        if ratings_url:
            from urllib.parse import urlparse
            parsed = urlparse(ratings_url)
            env["RATINGS_HOSTNAME"] = parsed.hostname or "ratings"
            env["RATINGS_SERVICE_PORT"] = str(parsed.port or 9080)
            env["ENABLE_RATINGS"] = "true"

        # Add star color based on version
        if self.config["version"] == "v2":
            env["STAR_COLOR"] = "black"
        elif self.config["version"] == "v3":
            env["STAR_COLOR"] = "red"

        return env


if __name__ == "__main__":
    main(ReviewsK8sCharm)