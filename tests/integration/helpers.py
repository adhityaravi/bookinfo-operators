"""Helper functions for Bookinfo integration tests."""

import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List

import jubilant

logger = logging.getLogger(__name__)

# Find terraform binary
TERRAFORM = shutil.which("terraform") or shutil.which("tofu")
if not TERRAFORM:
    raise RuntimeError("terraform or tofu binary not found in PATH")


def wait_for_active_idle_without_error(jujus: List[jubilant.Juju], timeout: int = 60 * 20):
    """
    Wait for all Juju models to be active and idle without errors.

    Args:
        jujus: List of Juju model instances to wait for
        timeout: Maximum time to wait for models to settle (default: 20 minutes)
    """
    for juju in jujus:
        logger.info(f"Waiting for the model ({juju.model}) to settle...")

        # Wait for all applications to be active
        juju.wait(
            jubilant.all_active, 
            delay=5,
            successes=5,
            timeout=timeout)

        # Wait for active state with error checking
        juju.wait(
            jubilant.all_active,
            delay=5,
            timeout=60 * 5,
            error=jubilant.any_error
        )

        # Wait for all agents to be idle with error checking
        juju.wait(
            jubilant.all_agents_idle,
            delay=5,
            timeout=60 * 5,
            error=jubilant.any_error,
        )

        logger.info(f"Model {juju.model} is active and idle")


def curl_service(
    juju: jubilant.Juju,
    unit: str,
    service_url: str,
    timeout: int = 30
) -> Dict[str, any]:
    """
    Execute a curl command from a Juju unit to test service connectivity.

    Args:
        juju: The Juju model instance
        unit: The unit to execute curl from (e.g., "productpage/0")
        service_url: The URL to curl (e.g., "http://details:9080/details/0")
        timeout: Command timeout in seconds (default: 30)

    Returns:
        Dictionary with stdout, stderr, and returncode
    """
    cmd = [
        "juju", "exec",
        "--model", juju.model,
        "--unit", unit,
        "--",
        "curl", "-s", "-w", "\\nHTTP_CODE:%{http_code}",
        service_url
    ]

    logger.info(f"Executing curl from {unit} to {service_url}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

    return {
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode
    }


def verify_http_success(curl_result: Dict[str, any]) -> None:
    """
    Verify that a curl result indicates HTTP success (200 OK).

    Args:
        curl_result: Dictionary returned from curl_service()

    Raises:
        AssertionError: If the request did not succeed
    """
    assert curl_result["returncode"] == 0, \
        f"Curl command failed: {curl_result['stderr']}"

    stdout = curl_result["stdout"]
    assert "HTTP_CODE:200" in stdout, \
        f"Expected HTTP 200, got: {stdout}"


def deploy_istio(juju: jubilant.Juju, channel: str = "2/edge") -> None:
    """
    Deploy istio-k8s to a Juju model using terraform.

    Args:
        juju: The Juju model instance to deploy to
        channel: The channel to deploy istio from (default: "latest/edge")
    """
    terraform_dir = Path(__file__).parent / "terraform" / "istio"
    state_file = Path(tempfile.gettempdir()) / f"istio-{juju.model}.tfstate"

    logger.info(f"Deploying istio-k8s to model {juju.model} from channel {channel}")
    logger.info(f"Using temporary state file: {state_file}")

    # Initialize terraform
    result = subprocess.run(
        [TERRAFORM, "init"],
        cwd=terraform_dir,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        logger.error(f"Terraform init failed:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}")
        raise RuntimeError(f"Terraform init failed with code {result.returncode}")

    # Apply terraform configuration
    env = os.environ.copy()
    env.update({
        "TF_VAR_model": juju.model,
        "TF_VAR_channel": channel,
    })

    result = subprocess.run(
        [TERRAFORM, "apply", "-auto-approve", f"-state={state_file}"],
        cwd=terraform_dir,
        capture_output=True,
        text=True,
        env=env,
    )
    if result.returncode != 0:
        logger.error(f"Terraform apply failed:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}")
        raise RuntimeError(f"Terraform apply failed with code {result.returncode}")

    # Wait for istio to be active
    logger.info("Waiting for istio to be active and idle...")
    wait_for_active_idle_without_error([juju], timeout=60 * 20)
    logger.info("Istio deployment complete")


def deploy_bookinfo(
    juju: jubilant.Juju,
    service_mesh: bool = False,
    channel: str = "latest/stable"
) -> None:
    """
    Deploy the bookinfo stack to a Juju model using terraform.

    Args:
        juju: The Juju model instance to deploy to
        service_mesh: Whether to enable service mesh integration (default: False)
        channel: The channel to deploy bookinfo from (default: "edge")
    """
    terraform_dir = Path(__file__).parent / "terraform" / "bookinfo"
    state_file = Path(tempfile.gettempdir()) / f"bookinfo-{juju.model}.tfstate"

    logger.info(
        f"Deploying bookinfo to model {juju.model} "
        f"(service_mesh={service_mesh}, channel={channel})"
    )
    logger.info(f"Using temporary state file: {state_file}")

    # Initialize terraform
    result = subprocess.run(
        [TERRAFORM, "init"],
        cwd=terraform_dir,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        logger.error(f"Terraform init failed:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}")
        raise RuntimeError(f"Terraform init failed with code {result.returncode}")

    # Apply terraform configuration
    env = os.environ.copy()
    env.update({
        "TF_VAR_model": juju.model,
        "TF_VAR_channel": channel,
        "TF_VAR_service_mesh": str(service_mesh).lower(),
    })

    result = subprocess.run(
        [TERRAFORM, "apply", "-auto-approve", f"-state={state_file}"],
        cwd=terraform_dir,
        capture_output=True,
        text=True,
        env=env,
    )
    if result.returncode != 0:
        logger.error(f"Terraform apply failed:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}")
        raise RuntimeError(f"Terraform apply failed with code {result.returncode}")

    # Wait for all applications to be active
    logger.info("Waiting for bookinfo to be active and idle...")
    wait_for_active_idle_without_error([juju], timeout=60 * 20)
    logger.info("Bookinfo deployment complete")
