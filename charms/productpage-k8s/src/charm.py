#!/usr/bin/env python3

import socket
import logging
from urllib.parse import urlparse
from typing import Dict, Optional

from ops.charm import CharmBase, ActionEvent
from ops.framework import StoredState
from ops.main import main
from ops.model import ActiveStatus, BlockedStatus, MaintenanceStatus, WaitingStatus
from ops.pebble import LayerDict

from charms.traefik_k8s.v2.ingress import IngressPerAppRequirer
from charms.bookinfo_lib.v0.bookinfo_service import BookinfoServiceConsumer

logger = logging.getLogger(__name__)


class ProductPageK8sCharm(CharmBase):
    """Charm for the Product Page microservice."""

    _stored = StoredState()
    
    # WSGI wrapper template for handling path prefixes
    WRAPPER_TEMPLATE = '''#!/usr/bin/env python3
import re
from productpage import app as original_app

# Path prefix from ingress
PREFIX = "{prefix}"

class PathPrefixMiddleware:
    """Middleware to handle path prefixes for hardcoded URLs."""
    
    def __init__(self, app, prefix):
        self.app = app
        self.prefix = prefix
    
    def __call__(self, environ, start_response):
        # Buffer to capture response details
        response_data = []
        
        def custom_start_response(status, headers, exc_info=None):
            response_data.append((status, headers))
            return start_response(status, headers, exc_info)
        
        # Get response from app
        app_iter = self.app(environ, custom_start_response)
        
        # Check if this is an HTML response
        if response_data:
            headers = dict(response_data[0][1])
            content_type = headers.get('Content-Type', '')
            
            # Only process HTML responses
            if 'text/html' in content_type:
                return self._fix_paths(app_iter)
        
        return app_iter
    
    def _fix_paths(self, app_iter):
        """Fix hardcoded paths in HTML responses."""
        try:
            # Collect response body
            response_body = b''.join(app_iter)
            
            # Convert to string for processing
            body_str = response_body.decode('utf-8')
            
            # Fix hardcoded paths
            # Replace href="/logout" with href="{prefix}/logout"
            body_str = re.sub(r'href="/logout"', f'href="{{self.prefix}}/logout"', body_str)
            
            # Replace action="login" with absolute path including prefix
            body_str = re.sub(r'action="login"', f'action="{{self.prefix}}/login"', body_str)
            
            # Replace /static/ paths  
            body_str = re.sub(r'(src|href)="/static/', r'\\1="' + self.prefix + '/static/', body_str)
            
            # Return modified response
            yield body_str.encode('utf-8')
        finally:
            # Close original iterator
            if hasattr(app_iter, 'close'):
                app_iter.close()

# Apply middleware if prefix exists
if PREFIX:
    app = PathPrefixMiddleware(original_app, PREFIX)
else:
    app = original_app
'''

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
        self.framework.observe(
            self._ingress.on.ready,
            self._on_ingress_ready
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

    def _on_ingress_ready(self, event):
        """Handle ingress is ready event"""
        self._update_layer()
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

        # Create wrapper to handle path prefix if we have an ingress
        if self._ingress.url:
            self._create_wsgi_wrapper()
        
        layer = self._generate_layer()
        self.container.add_layer("productpage", layer, combine=True)
        
        try:
            self.container.replan()
            logger.info("Service layer updated")
        except Exception as e:
            logger.error(f"Failed to replan service: {e}")
            self.unit.status = BlockedStatus(f"Failed to start service: {e}")

    def _create_wsgi_wrapper(self):
        """Create a WSGI wrapper that fixes hardcoded URLs for path prefix support."""
        # Get the path prefix from ingress URL
        prefix = ""
        if ingress_url := self._ingress.url:
            parsed = urlparse(ingress_url)
            if parsed.path and parsed.path != '/':
                prefix = parsed.path.rstrip('/')
        
        # Generate wrapper content from template
        wrapper_content = self.WRAPPER_TEMPLATE.format(prefix=prefix)
        
        try:
            self.container.push("/opt/microservices/productpage_wrapper.py", wrapper_content, make_dirs=True)
            logger.info(f"Created WSGI wrapper with prefix: {prefix}")
        except Exception as e:
            logger.error(f"Failed to create wrapper: {e}")

    def _generate_layer(self) -> LayerDict:
        """Generate the Pebble layer configuration."""
        # Use wrapper if we have ingress (to handle path prefix)
        app_module = "productpage_wrapper:app" if self._ingress.url else "productpage:app"
        return {
            "summary": "Product Page service layer",
            "description": "Pebble layer for the Product Page microservice",
            "services": {
                "productpage": {
                    "override": "replace",
                    "summary": "Product Page service",
                    "command": f"gunicorn -b \"[::]\":{self.config['port']} {app_module} -w 8 --keep-alive 2 -k gevent --forwarded-allow-ips='*'",
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
        if not output.endswith('/'):
            output = output + '/'
        # NOTE: just give the user the product page url instead of the overview since redirect isnt working right.
        output = output + "productpage?u=normal"
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
            # Experimental: log level may not actually affect the service logging
            "LOG_LEVEL": self.config["log-level"],
            "FLOOD_FACTOR": str(self.config["flood-factor"]),
        }

        # Extract hostname and port from URLs for upstream compatibility
        details_url = self._get_details_url()
        if details_url:
            parsed = urlparse(details_url)
            env["DETAILS_HOSTNAME"] = parsed.hostname or "details"  # just use upstream defaults for sanity
            env["DETAILS_SERVICE_PORT"] = str(parsed.port or 9080)

        reviews_url = self._get_reviews_url()
        if reviews_url:
            parsed = urlparse(reviews_url)
            env["REVIEWS_HOSTNAME"] = parsed.hostname or "reviews"
            env["REVIEWS_SERVICE_PORT"] = str(parsed.port or 9080)
        ratings_url = self._get_ratings_url()
        if ratings_url:
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
