"""HTTP proxy utilities for China mainland network access."""

import os
from typing import Optional

import httpx


def get_proxy_url() -> Optional[str]:
    """Read proxy environment variables.

    Returns the HTTPS proxy if set, otherwise the HTTP proxy, or None.
    """
    return os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY") or None


def create_http_client(
    timeout_seconds: float = 120.0,
    proxy_required: bool = False,
) -> httpx.AsyncClient:
    """Create an HTTP client with proxy configuration for external API calls.

    Args:
        timeout_seconds: Request timeout in seconds.
        proxy_required: If True, raise error when no proxy is configured.

    Returns:
        Configured httpx.AsyncClient instance.
    """
    proxy_url = get_proxy_url()

    if proxy_required and not proxy_url:
        raise RuntimeError("Proxy is required but HTTP_PROXY/HTTPS_PROXY are not set")

    return httpx.AsyncClient(
        proxy=proxy_url,
        timeout=httpx.Timeout(timeout_seconds),
    )
