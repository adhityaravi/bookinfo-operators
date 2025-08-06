#!/usr/bin/env python3

import logging
from typing import Dict, Optional
from urllib.parse import urlparse

from ops.charm import CharmBase
from ops.framework import StoredState
from ops.main import main
from ops.model import ActiveStatus, BlockedStatus, MaintenanceStatus, WaitingStatus
from ops.pebble import LayerDict

from charms.bookinfo_lib.v0.bookinfo_service import BookinfoServiceProvider, BookinfoServiceConsumer
from charms.istio_beacon_k8s.v0.service_mesh import ServiceMeshConsumer, Method, Endpoint, AppPolicy

logger = logging.getLogger(__name__)

PORT = 9080
SUPPORTED_VERSIONS = ["v1", "v2", "v3"]


class ReviewsK8sCharm(CharmBase):
    """Charm for the Reviews microservice."""

    _stored = StoredState()

    def __init__(self, *args):
        super().__init__(*args)
        self._stored.set_default(pebble_ready=False)

        self.container = self.unit.get_container("bookinfo-reviews")

        # Core event handlers
        self.framework.observe(self.on.bookinfo_reviews_pebble_ready, self._on_pebble_ready)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.on.update_status, self._on_update_status)

        # Service provider
        self.service_provider = BookinfoServiceProvider(
            self,
            "reviews",
            PORT
        )

        # Service consumer
        self.ratings_consumer = BookinfoServiceConsumer(self, "ratings")
        self.framework.observe(self.ratings_consumer.on.url_changed, self._on_relation_changed)

        # Service mesh with authorization policies
        self._mesh = ServiceMeshConsumer(
            self,
            policies=[
                AppPolicy(
                    relation="reviews",
                    endpoints=[
                        Endpoint(
                            ports=[PORT],
                            methods=[Method.get],
                            paths=["/health", "/reviews/*"]
                        )
                    ]
                )
            ]
        )
        
        # Initial port configuration
        self._set_ports()

    def _on_pebble_ready(self, event):
        """Handle the pebble ready event."""
        self._stored.pebble_ready = True
        self._reconcile()

    def _on_config_changed(self, event):
        """Handle config changed event."""
        self._reconcile()

    def _on_update_status(self, event):
        """Handle update status event."""
        self._reconcile()

    def _on_relation_changed(self, event):
        """Handle any relation changed event."""
        self._reconcile()

    def _reconcile(self):
        """Reconcile the charm state.
        
        This is the main reconciliation loop that ensures the charm
        converges to the desired state regardless of which event triggered it.
        """
        # Validate configuration first
        if not self._validate_config():
            self.unit.status = BlockedStatus(f"Invalid version: {self.config['version']}")
            return

        # Check if pebble is ready
        if not self._stored.pebble_ready:
            self.unit.status = WaitingStatus("Waiting for pebble ready")
            return

        if not self.container.can_connect():
            self.unit.status = MaintenanceStatus("Waiting for container")
            return

        # Check if required relations are available
        version = self.config["version"]
        ratings_url = self._get_ratings_url()
        
        if version in ["v2", "v3"] and not ratings_url:
            self.unit.status = WaitingStatus(f"Version {version} requires ratings service")
            return

        # Update configuration
        try:
            self._update_layer()
            self._set_ports()
            
            # Check if service is running
            service = self.container.get_service("reviews")
            if service.is_running():
                status_msg = f"Running version {version}"
                if ratings_url:
                    status_msg += " with ratings"
                self.unit.status = ActiveStatus(status_msg)
            else:
                self.unit.status = MaintenanceStatus("Service not running")
        except Exception as e:
            logger.error(f"Failed to reconcile: {e}")
            self.unit.status = BlockedStatus(f"Failed to reconcile: {str(e)}")

    def _validate_config(self) -> bool:
        """Validate configuration."""
        return self.config["version"] in SUPPORTED_VERSIONS

    def _get_ratings_url(self) -> Optional[str]:
        """Get the ratings service URL directly from relation data."""
        try:
            # Get the first relation for ratings (typically only one)
            relations = self.model.relations.get("ratings", [])
            if relations:
                relation = relations[0]  # Take the first relation
                return relation.data[relation.app].get("url")
        except Exception as e:
            logger.warning(f"Failed to get ratings URL: {e}")
        return None

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
            raise

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

    def _get_environment(self) -> Dict[str, str]:
        """Get environment variables for the service."""
        env = {
            "SERVICE_NAME": "reviews",
            "SERVICE_VERSION": self.config["version"],
            "LOG_DIR": "/tmp/logs",
            "SERVERDIRNAME": "reviews",
            # Experimental: log level may not actually affect the service logging
            "LOG_LEVEL": self.config["log-level"],
        }

        # Extract hostname and port from URL for upstream compatibility
        ratings_url = self._get_ratings_url()
        if ratings_url:
            parsed = urlparse(ratings_url)
            env["RATINGS_HOSTNAME"] = parsed.hostname or "ratings"
            env["RATINGS_SERVICE_PORT"] = str(parsed.port or PORT)
            env["ENABLE_RATINGS"] = "true"

        # Add star color based on version
        if self.config["version"] == "v2":
            env["STAR_COLOR"] = "black"
        elif self.config["version"] == "v3":
            env["STAR_COLOR"] = "red"

        return env

    def _set_ports(self):
        """Open the application ports to fix Juju's 65535 placeholder issue."""
        try:
            self.unit.open_port("tcp", PORT)
            logger.info(f"Opened TCP port {PORT}")
        except Exception as e:
            logger.warning(f"Failed to open port: {e}")


if __name__ == "__main__":
    main(ReviewsK8sCharm)
