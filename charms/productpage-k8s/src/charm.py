#!/usr/bin/env python3

import socket
import logging
from typing import Dict, Optional

from ops.charm import CharmBase, ActionEvent
from ops.framework import StoredState
from ops.main import main
from ops.model import ActiveStatus, BlockedStatus, MaintenanceStatus, WaitingStatus
from ops.pebble import LayerDict

from charms.traefik_k8s.v2.ingress import IngressPerAppRequirer
from charms.bookinfo_lib.v0.bookinfo_service import BookinfoServiceConsumer

logger = logging.getLogger(__name__)

PRODUCTPAGE_PORT = 9080


class ProductPageK8sCharm(CharmBase):
    """Charm for the Product Page microservice."""

    _stored = StoredState()

    def __init__(self, *args):
        super().__init__(*args)
        self._stored.set_default(
            started=False,
            details_url=None,
            reviews_url=None,
            ratings_url=None
        )

        self.container = self.unit.get_container("productpage")

        self.framework.observe(self.on.productpage_pebble_ready, self._on_pebble_ready)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.on.update_status, self._on_update_status)

        self._ingress = IngressPerAppRequirer(
            charm=self,
            port=self.config["port"],
            strip_prefix=True,
            redirect_https=True,
            scheme='http',
        )

        # Consume details and reviews services
        self._details_consumer = BookinfoServiceConsumer(self, "details")
        self.framework.observe(
            self._details_consumer.on.url_changed,
            self._on_details_url_changed
        )

        self._reviews_consumer = BookinfoServiceConsumer(self, "reviews")
        self.framework.observe(
            self._reviews_consumer.on.url_changed,
            self._on_reviews_url_changed
        )

        self._ratings_consumer = BookinfoServiceConsumer(self, "ratings")
        self.framework.observe(
            self._ratings_consumer.on.url_changed,
            self._on_ratings_url_changed
        )

        self.framework.observe(self.on.get_url_action, self._get_url)

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

    def _on_details_url_changed(self, event):
        """Handle details URL changed."""
        self._stored.details_url = event.url
        if event.url:
            logger.info(f"Details service available at: {event.url}")
        else:
            logger.info("Details service unavailable")
        self._update_layer()
        self._update_status()

    def _on_reviews_url_changed(self, event):
        """Handle reviews URL changed."""
        self._stored.reviews_url = event.url
        if event.url:
            logger.info(f"Reviews service available at: {event.url}")
        else:
            logger.info("Reviews service unavailable")
        self._update_layer()
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

    def _update_status(self):
        """Update the charm status."""
        if not self._stored.started:
            self.unit.status = MaintenanceStatus("Waiting for pebble ready")
            return

        if not self.container.can_connect():
            self.unit.status = MaintenanceStatus("Waiting for container")
            return

        available_services = []
        if self._get_details_url():
            available_services.append("details")
        if self._get_reviews_url():
            available_services.append("reviews")
        if self._get_ratings_url():
            available_services.append("ratings")

        if len(available_services) < 1:
            self.unit.status = WaitingStatus(f"Waiting for atleast 1 backend service relation")
            return

        try:
            service = self.container.get_service("productpage")
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
        self.container.add_layer("productpage", layer, combine=True)
        
        try:
            self.container.replan()
            logger.info("Service layer updated")
        except Exception as e:
            logger.error(f"Failed to replan service: {e}")
            self.unit.status = BlockedStatus(f"Failed to start service: {e}")

    def _generate_layer(self) -> LayerDict:
        """Generate the Pebble layer configuration."""
        return {
            "summary": "Product Page service layer",
            "description": "Pebble layer for the Product Page microservice",
            "services": {
                "productpage": {
                    "override": "replace",
                    "summary": "Product Page service",
                    "command": f"python /opt/microservices/productpage.py {self.config['port']}",
                    "startup": "enabled",
                    "environment": self._get_environment(),
                }
            },
        }

    def _get_details_url(self) -> Optional[str]:
        """Get the details service URL."""
        return self._stored.details_url

    def _get_reviews_url(self) -> Optional[str]:
        """Get the reviews service URL."""
        return self._stored.reviews_url

    def _get_ratings_url(self) -> Optional[str]:
        """Get the ratings service URL."""
        return self._stored.ratings_url

    def _get_url(self, event: ActionEvent):
        """Return the external hostname to be passed to ingress via the relation.

        If we do not have an ingress, then use the pod dns name as hostname.
        Relying on cluster's DNS service, those dns names are routable virtually
        exclusively inside the cluster.
        """
        output = self._internal_url
        if ingress_url := self._ingress.url:
            output = ingress_url
        # FIXME: the upstream application doesnt seem to support path prefixes. 
        # So redirecting from the microservice architecture page to the actual bookinfo 
        # app when ingressed fails. For now simply show only the app page url when url is requested 
        output = output + "/productpage?u=normal"
        event.set_results(
            {
                "url": output,
            }
        )

    def _get_environment(self) -> Dict[str, str]:
        """Get environment variables for the service."""
        env = {
            "SERVICE_NAME": "productpage",
            "SERVICE_VERSION": "v1",
            "LOG_LEVEL": self.config["log-level"],
            "FLOOD_FACTOR": str(self.config["flood-factor"]),
        }

        # Extract hostname and port from URLs for upstream compatibility
        details_url = self._get_details_url()
        if details_url:
            from urllib.parse import urlparse
            parsed = urlparse(details_url)
            env["DETAILS_HOSTNAME"] = parsed.hostname or "details"  # just use upstream defaults for sanity
            env["DETAILS_SERVICE_PORT"] = str(parsed.port or 9080)

        reviews_url = self._get_reviews_url()
        if reviews_url:
            from urllib.parse import urlparse
            parsed = urlparse(reviews_url)
            env["REVIEWS_HOSTNAME"] = parsed.hostname or "reviews"
            env["REVIEWS_SERVICE_PORT"] = str(parsed.port or 9080)

        ratings_url = self._get_ratings_url()
        if ratings_url:
            from urllib.parse import urlparse
            parsed = urlparse(ratings_url)
            env["RATINGS_HOSTNAME"] = parsed.hostname or "ratings"
            env["RATINGS_SERVICE_PORT"] = str(parsed.port or 9080)

        return env

    @property
    def _internal_url(self) -> str:
        """Return the fqdn dns-based in-cluster (private) address of the catalogue server."""
        scheme = "http"
        port = self.config["port"]
        return f"{scheme}://{socket.getfqdn()}:{port}"


if __name__ == "__main__":
    main(ProductPageK8sCharm)
