"""Integration tests for bookinfo reviews charm."""

import jubilant

APP_NAME = "bookinfo-reviews-k8s"


def test_reviews_deploy(juju, charm, resources):
    """Test basic deployment of reviews charm."""
    juju.deploy(charm, resources=resources)
    juju.wait(jubilant.all_active)
    
    status = juju.status()
    assert APP_NAME in status.apps
    assert status.apps[APP_NAME].is_active


def test_reviews_service_running(juju, charm, resources):
    """Test that the reviews service is properly running."""
    status = juju.status()
    unit_name = f"{APP_NAME}/0"
    
    assert status.apps[APP_NAME].units[unit_name].is_active


def test_reviews_health_endpoint(juju, charm, resources):
    """Test reviews service health endpoint returns 200."""
    # Use curl with -w flag to get HTTP status code
    result = juju.cli("exec", "--unit", f"{APP_NAME}/0", "--", 
                      "curl", "-s", "-w", "%{http_code}", "-o", "/dev/null",
                      "http://localhost:9080/health")
    
    # Should return "200"
    assert result.strip() == "200"


def test_reviews_api_endpoint(juju, charm, resources):
    """Test reviews API endpoint returns JSON response."""
    # Test the reviews endpoint with a sample book ID
    result = juju.cli("exec", "--unit", f"{APP_NAME}/0", "--", 
                      "curl", "-s",
                      "http://localhost:9080/reviews/123")
    
    # Should contain reviews data (basic check for JSON-like response)
    assert "reviews" in result or "review" in result or "id" in result