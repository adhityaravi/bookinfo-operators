"""Integration tests for bookinfo ratings charm."""

import jubilant

APP_NAME = "bookinfo-ratings-k8s"


def test_ratings_deploy(juju, charm, resources):
    """Test basic deployment of ratings charm."""
    juju.deploy(charm, resources=resources)
    juju.wait(jubilant.all_active)

    status = juju.status()
    assert APP_NAME in status.apps
    assert status.apps[APP_NAME].is_active


def test_ratings_service_running(juju, charm, resources):
    """Test that the ratings service is properly running."""
    status = juju.status()
    unit_name = f"{APP_NAME}/0"

    assert status.apps[APP_NAME].units[unit_name].is_active


def test_ratings_health_endpoint(juju, charm, resources):
    """Test ratings service health endpoint returns 200."""
    # Use curl with -w flag to get HTTP status code
    result = juju.cli(
        "exec",
        "--unit",
        f"{APP_NAME}/0",
        "--",
        "curl",
        "-s",
        "-w",
        "%{http_code}",
        "-o",
        "/dev/null",
        "http://localhost:9080/health",
    )

    # Should return "200"
    assert result.strip() == "200"


def test_ratings_api_endpoint(juju, charm, resources):
    """Test ratings API endpoint returns JSON response."""
    # Test the ratings endpoint with a sample book ID
    result = juju.cli(
        "exec",
        "--unit",
        f"{APP_NAME}/0",
        "--",
        "curl",
        "-s",
        "-w",
        "%{http_code}",
        "http://localhost:9080/ratings/123",
    )

    # Should contain ratings data (basic check for JSON-like response)
    assert "rating" in result or "stars" in result or "200" in result
