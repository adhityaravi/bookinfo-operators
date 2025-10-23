"""Integration tests for Bookinfo application stack."""

import logging

import pytest
from pytest_bdd import given, when, then, scenarios, parsers
import jubilant

from helpers import (
    wait_for_active_idle_without_error,
    curl_service,
    verify_http_success,
    deploy_istio,
    deploy_bookinfo,
)

logger = logging.getLogger(__name__)

# Load all scenarios from the feature file
scenarios("features/bookinfo.feature")


# Background steps
@given("a k8s model for bookinfo")
def k8s_model_bookinfo(bookinfo_juju: jubilant.Juju):
    """Ensure the bookinfo Juju model exists."""
    assert bookinfo_juju.model is not None
    logger.info(f"Bookinfo model created: {bookinfo_juju.model}")


@given("an istio-system model with istio-k8s deployed")
def istio_system_deployed(istio_system_juju: jubilant.Juju):
    """Ensure the istio-system model exists with istio-k8s deployed."""
    assert istio_system_juju.model is not None
    logger.info(f"Istio-system model created: {istio_system_juju.model}")

    # Deploy istio-k8s
    deploy_istio(istio_system_juju)


# Deployment steps
@when(parsers.parse("you deploy the bookinfo stack {mesh_enabled}"))
def deploy_bookinfo_stack(mesh_enabled: str, bookinfo_juju: jubilant.Juju):
    """Deploy the bookinfo stack with the specified service_mesh setting."""
    # Convert string "true"/"false" to Python boolean
    service_mesh_bool = mesh_enabled.lower() == "with service mesh"
    logger.info(f"Deploying bookinfo stack with service_mesh={service_mesh_bool}")

    # Deploy bookinfo
    deploy_bookinfo(bookinfo_juju, service_mesh=service_mesh_bool)


@given(parsers.parse("the bookinfo stack is deployed {mesh_enabled}"))
def bookinfo_stack_deployed(mesh_enabled: str, bookinfo_juju: jubilant.Juju):
    """Ensure the bookinfo stack is deployed with the specified service_mesh setting."""
    # Convert string "true"/"false" to Python boolean
    service_mesh_bool = mesh_enabled.lower() == "with service mesh"
    logger.info(f"Bookinfo stack is deployed with service_mesh={service_mesh_bool}")

    # Deploy bookinfo
    deploy_bookinfo(bookinfo_juju, service_mesh=service_mesh_bool)


# Status verification steps
@then("all charms are active")
def all_charms_active(bookinfo_juju: jubilant.Juju):
    """Verify all deployed charms are in active state."""
    wait_for_active_idle_without_error([bookinfo_juju], timeout=60 * 20)


# Connectivity test steps
@when("productpage calls the details service")
def productpage_calls_details(bookinfo_juju: jubilant.Juju, juju_run_output: dict):
    """Test connectivity from productpage to details service using curl."""
    result = curl_service(
        juju=bookinfo_juju,
        unit="productpage/0",
        service_url="http://details:9080/details/0"
    )
    juju_run_output["details"] = result
    logger.info(f"Productpage -> Details curl result: {result['stdout']}")


@when("productpage calls the reviews service")
def productpage_calls_reviews(bookinfo_juju: jubilant.Juju, juju_run_output: dict):
    """Test connectivity from productpage to reviews service using curl."""
    result = curl_service(
        juju=bookinfo_juju,
        unit="productpage/0",
        service_url="http://reviews:9080/reviews/0"
    )
    juju_run_output["reviews"] = result
    logger.info(f"Productpage -> Reviews curl result: {result['stdout']}")


@when("reviews calls the ratings service")
def reviews_calls_ratings(bookinfo_juju: jubilant.Juju, juju_run_output: dict):
    """Test connectivity from reviews to ratings service using curl."""
    result = curl_service(
        juju=bookinfo_juju,
        unit="reviews/0",
        service_url="http://ratings:9080/ratings/0"
    )
    juju_run_output["ratings"] = result
    logger.info(f"Reviews -> Ratings curl result: {result['stdout']}")


# Response verification steps
@then("the request succeeds")
def request_succeeds(juju_run_output: dict):
    """Verify the last request succeeded with HTTP 200."""
    # Get the most recent curl result
    latest_result = list(juju_run_output.values())[-1] if juju_run_output else None
    assert latest_result is not None, "No curl result found"

    verify_http_success(latest_result)


@then("details returns valid book information")
def details_returns_book_info(juju_run_output: dict):
    """Verify the details service returned valid book information."""
    result = juju_run_output.get("details")
    assert result is not None, "No details result found"

    stdout = result["stdout"]
    # Check for expected book information fields (JSON response)
    assert any(field in stdout for field in ["id", "type", "year", "ISBN"]), \
        f"Response missing book information: {stdout}"
    logger.info(f"Details response: {stdout}")


@then("reviews returns book reviews")
def reviews_returns_reviews(juju_run_output: dict):
    """Verify the reviews service returned book reviews."""
    result = juju_run_output.get("reviews")
    assert result is not None, "No reviews result found"

    stdout = result["stdout"]
    # Check for expected reviews information (JSON response)
    assert any(field in stdout for field in ["reviews", "id"]), \
        f"Response missing reviews information: {stdout}"
    logger.info(f"Reviews response: {stdout}")
