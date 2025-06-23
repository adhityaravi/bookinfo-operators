#!/usr/bin/env python3

import logging
from typing import Dict

from ops.charm import CharmBase
from ops.framework import StoredState
from ops.main import main
from ops.model import ActiveStatus, BlockedStatus, MaintenanceStatus, WaitingStatus
from ops.pebble import LayerDict

from charms.bookinfo_lib.v0.bookinfo_service import BookinfoServiceProvider
from charms.istio_beacon_k8s.v0.service_mesh import ServiceMeshConsumer, Method, Endpoint, Policy

logger = logging.getLogger(__name__)

PORT = 9080


class RatingsK8sCharm(CharmBase):
    """Charm for the Ratings microservice."""

    _stored = StoredState()

    def __init__(self, *args):
        super().__init__(*args)
        self._stored.set_default(pebble_ready=False)

        self.container = self.unit.get_container("bookinfo-ratings")

        # Core event handlers
        self.framework.observe(self.on.bookinfo_ratings_pebble_ready, self._on_pebble_ready)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.on.update_status, self._on_update_status)

        # Service provider
        self.service_provider = BookinfoServiceProvider(
            self,
            "ratings",
            PORT
        )

        # Service mesh with authorization policies
        self._mesh = ServiceMeshConsumer(
            self,
            policies=[
                Policy(
                    relation="ratings",
                    endpoints=[
                        Endpoint(
                            ports=[PORT],
                            methods=[Method.get],
                            paths=["/health", "/ratings/*"]
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

    def _reconcile(self):
        """Reconcile the charm state.
        
        This is the main reconciliation loop that ensures the charm
        converges to the desired state regardless of which event triggered it.
        """
        # Update status first
        if not self._stored.pebble_ready:
            self.unit.status = WaitingStatus("Waiting for pebble ready")
            return

        if not self.container.can_connect():
            self.unit.status = MaintenanceStatus("Waiting for container")
            return

        # Update configuration
        try:
            self._update_layer()
            self._set_ports()
            
            # Check if service is running
            service = self.container.get_service("ratings")
            if service.is_running():
                self.unit.status = ActiveStatus("Ready")
            else:
                self.unit.status = MaintenanceStatus("Service not running")
        except Exception as e:
            logger.error(f"Failed to reconcile: {e}")
            self.unit.status = BlockedStatus(f"Failed to reconcile: {str(e)}")

    def _update_layer(self):
        """Update the Pebble layer configuration."""
        if not self.container.can_connect():
            logger.debug("Cannot connect to container")
            return

        layer = self._generate_layer()
        self.container.add_layer("ratings", layer, combine=True)
        
        try:
            self.container.replan()
            logger.info("Service layer updated")
        except Exception as e:
            logger.error(f"Failed to replan service: {e}")
            raise

    def _generate_layer(self) -> LayerDict:
        """Generate the Pebble layer configuration."""
        return {
            "summary": "Ratings service layer",
            "description": "Pebble layer for the Ratings microservice",
            "services": {
                "ratings": {
                    "override": "replace",
                    "summary": "Ratings service",
                    "command": f"node /opt/microservices/ratings.js {PORT}",
                    "startup": "enabled",
                    "environment": self._get_environment(),
                }
            },
        }

    def _get_environment(self) -> Dict[str, str]:
        """Get environment variables for the service."""
        env = {
            "SERVICE_NAME": "ratings",
            "SERVICE_VERSION": "v1",
            # Experimental: log level may not actually affect the service logging
            "LOG_LEVEL": self.config["log-level"],
        }
        return env

    def _set_ports(self):
        """Open the application ports to fix Juju's 65535 placeholder issue."""
        try:
            self.unit.open_port("tcp", PORT)
            logger.info(f"Opened TCP port {PORT}")
        except Exception as e:
            logger.warning(f"Failed to open port: {e}")


if __name__ == "__main__":
    main(RatingsK8sCharm)
