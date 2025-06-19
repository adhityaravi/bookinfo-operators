#!/usr/bin/env python3

import logging
from typing import Dict

from ops.charm import CharmBase
from ops.framework import StoredState
from ops.main import main
from ops.model import ActiveStatus, BlockedStatus, MaintenanceStatus
from ops.pebble import LayerDict

from charms.bookinfo_lib.v0.bookinfo_service import BookinfoServiceProvider

logger = logging.getLogger(__name__)

DETAILS_PORT = 9080


class DetailsK8sCharm(CharmBase):
    """Charm for the Details microservice."""

    _stored = StoredState()

    def __init__(self, *args):
        super().__init__(*args)
        self._stored.set_default(started=False)

        self.container = self.unit.get_container("details")

        self.framework.observe(self.on.details_pebble_ready, self._on_pebble_ready)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.on.update_status, self._on_update_status)

        self.service_provider = BookinfoServiceProvider(
            charm=self,
            relation_name="details",
            port=self.config["port"]
        )

    def _on_pebble_ready(self, event):
        """Handle the pebble ready event."""
        self._update_layer()
        self._stored.started = True
        self.unit.status = ActiveStatus()

    def _on_config_changed(self, event):
        """Handle config changed event."""
        if not self._stored.started:
            event.defer()
            return

        self._update_layer()
        self.unit.status = ActiveStatus()

    def _on_update_status(self, event):
        """Handle update status event."""
        if not self._stored.started:
            self.unit.status = MaintenanceStatus("Waiting for pebble ready")
            return

        if not self.container.can_connect():
            self.unit.status = MaintenanceStatus("Waiting for container")
            return

        try:
            service = self.container.get_service("details")
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
        self.container.add_layer("details", layer, combine=True)
        
        try:
            self.container.replan()
            logger.info("Service layer updated")
        except Exception as e:
            logger.error(f"Failed to replan service: {e}")
            self.unit.status = BlockedStatus(f"Failed to start service: {e}")

    def _generate_layer(self) -> LayerDict:
        """Generate the Pebble layer configuration."""
        return {
            "summary": "Details service layer",
            "description": "Pebble layer for the Details microservice",
            "services": {
                "details": {
                    "override": "replace",
                    "summary": "Details service",
                    "command": "ruby /opt/microservices/details.rb " + str(self.config["port"]),
                    "startup": "enabled",
                    "environment": self._get_environment(),
                }
            },
        }

    def _get_environment(self) -> Dict[str, str]:
        """Get environment variables for the service."""
        env = {
            "SERVICE_NAME": "details",
            "SERVICE_VERSION": "v1",
            "LOG_LEVEL": self.config["log-level"],
        }


        return env


if __name__ == "__main__":
    main(DetailsK8sCharm)
