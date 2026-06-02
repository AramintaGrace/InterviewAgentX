"""HTTP proxy utilities for China mainland network access."""

import os
from typing import Optional

import httpx


def get_proxy_config() -> dict:
    """Read proxy environment variables and return httpx-compatible mapping."""
    proxies = {}
    http_proxy = os.environ.get("HTTP_PROXY")
    https_proxy = os.environ.get("HTTPS_PROXY")
    if http_proxy:
        proxies["http://"] = http_proxy
    if https_proxy:
        proxies["https://"] = https_proxy
    return proxies


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
    proxies = get_proxy_config()
    has_proxy = any(proxies.values())

    if proxy_required and not has_proxy:
        raise RuntimeError("Proxy is required but HTTP_PROXY/HTTPS_PROXY are not set")

    return httpx.AsyncClient(
        proxies=proxies if has_proxy else None,
        timeout=httpx.Timeout(timeout_seconds),
    )
