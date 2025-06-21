#!/usr/bin/env python3

import logging
from typing import Dict, Optional

from ops.charm import CharmBase
from ops.framework import StoredState
from ops.main import main
from ops.model import ActiveStatus, BlockedStatus, MaintenanceStatus, WaitingStatus
from ops.pebble import LayerDict

from charms.bookinfo_lib.v0.bookinfo_service import BookinfoServiceProvider

logger = logging.getLogger(__name__)

PORT = 9080


class RatingsK8sCharm(CharmBase):
    """Charm for the Ratings microservice."""

    _stored = StoredState()

    def __init__(self, *args):
        super().__init__(*args)
        self._stored.set_default(
            started=False
        )

        self.container = self.unit.get_container("ratings")

        self.framework.observe(self.on.ratings_pebble_ready, self._on_pebble_ready)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.on.update_status, self._on_update_status)

        self.service_provider = BookinfoServiceProvider(
            self,
            "ratings",
            PORT
        )

    def _on_pebble_ready(self, event):
        """Handle the pebble ready event."""
        self._update_layer()
        self._stored.started = True
        self._update_status()

    def _on_config_changed(self, event):
        """Handle config changed event."""
        if not self._stored.started:
            event.defer()
            return

        self._update_layer()
        self._update_status()

    def _on_update_status(self, event):
        """Handle update status event."""
        self._update_status()


    def _update_status(self):
        """Update the charm status."""
        if not self._stored.started:
            self.unit.status = MaintenanceStatus("Waiting for pebble ready")
            return

        if not self.container.can_connect():
            self.unit.status = MaintenanceStatus("Waiting for container")
            return


        try:
            service = self.container.get_service("ratings")
            if service.is_running():
                self.unit.status = ActiveStatus()
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
        self.container.add_layer("ratings", layer, combine=True)
        
        try:
            self.container.replan()
            logger.info("Service layer updated")
        except Exception as e:
            logger.error(f"Failed to replan service: {e}")
            self.unit.status = BlockedStatus(f"Failed to start service: {e}")

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


if __name__ == "__main__":
    main(RatingsK8sCharm)
