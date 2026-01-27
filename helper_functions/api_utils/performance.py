"""Performance optimization module with connection pooling and request batching.

Provides session management for connection pooling and batch request coordination
to reduce overhead and improve API response times.
"""
from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from helper_functions.logging.logger_config import logger, track_api_call

if TYPE_CHECKING:
    from collections.abc import Callable

# Global session for connection pooling
_session: requests.Session | None = None


def get_session() -> requests.Session:
    """Get or create a global requests session with connection pooling.

    Benefits:
    - Connection pooling reduces TCP handshake overhead
    - Keep-alive connections reduce latency
    - Automatic connection reuse across requests
    - Configurable retry strategy for connection failures

    :return: Configured requests.Session with pooling and retry strategy
    """
    global _session

    if _session is None:
        _session = requests.Session()

        # Configure connection pooling
        # pool_connections: number of connection pools to cache
        # pool_maxsize: maximum number of connections to save in pool
        adapter = HTTPAdapter(
            pool_connections=10,  # Cache 10 connection pools
            pool_maxsize=20,  # Max 20 connections per pool
            max_retries=Retry(
                total=3,  # Total retries
                connect=2,  # Retries for connection errors
                read=2,  # Retries for read errors
                backoff_factor=0.3,  # Exponential backoff multiplier
                status_forcelist=[429, 500, 502, 503, 504],  # Retry on these HTTP statuses
            ),
        )

        # Mount adapter for both HTTP and HTTPS
        _session.mount("http://", adapter)
        _session.mount("https://", adapter)

        # Add timeout to prevent hanging connections
        _session.timeout = 10  # type: ignore[attr-defined]

        logger.info("Created global requests session with connection pooling")

    return _session


def close_session() -> None:
    """Close the global session and release connections.

    Call this during application shutdown to clean up resources.
    """
    global _session

    if _session is not None:
        _session.close()
        _session = None
        logger.info("Closed global requests session")


class RequestBatch:
    """Coordinator for batching multiple API requests to reduce overhead.

    Benefits:
    - Groups related requests together
    - Reuses connection across batch
    - Reduces context switching
    - Allows parallel requests within a batch (future enhancement)

    Example:
        batch = RequestBatch()
        batch.add_request('nba', lambda: get_nba_data(team))
        batch.add_request('nhl', lambda: get_nhl_data(team))
        results = batch.execute()  # Execute all requests efficiently

    """

    def __init__(self, name: str = "default", max_requests: int = 10) -> None:
        """Initialize request batch.

        :param name: Batch identifier for logging
        :param max_requests: Maximum requests per batch
        """
        self.name = name
        self.max_requests = max_requests
        self.requests: dict[str, tuple[Callable[[], Any], str]] = {}
        self.start_time: float | None = None

    def add_request(self, request_id: str, func: Callable[[], Any], endpoint: str = "unknown") -> None:
        """Add a request to the batch.

        :param request_id: Unique identifier for this request
        :param func: Callable that makes the API request
        :param endpoint: API endpoint name for tracking
        """
        if len(self.requests) >= self.max_requests:
            logger.warning(f"Batch '{self.name}' at capacity ({self.max_requests}), skipping request {request_id}")
            return

        self.requests[request_id] = (func, endpoint)
        logger.debug(f"Added request '{request_id}' to batch '{self.name}' ({len(self.requests)}/{self.max_requests})")

    def execute(self) -> dict[str, tuple[Any, float]]:
        """Execute all requests in the batch and track performance.

        Returns results in order they were added, with execution time per request.

        :return: Dict of {request_id: (result, duration_ms)}
        """
        self.start_time = time.time()
        results: dict[str, tuple[Any, float]] = {}

        logger.info(f"Executing batch '{self.name}' with {len(self.requests)} requests")

        for request_id, (func, endpoint) in self.requests.items():
            try:
                request_start = time.time()
                result = func()
                duration_ms = (time.time() - request_start) * 1000

                results[request_id] = (result, duration_ms)
                track_api_call(f"{endpoint}_batch", duration_ms, success=True)

                logger.debug(f"Request '{request_id}' completed in {duration_ms:.0f}ms")

            except Exception as e:
                duration_ms = (time.time() - request_start) * 1000
                results[request_id] = (None, duration_ms)
                track_api_call(f"{endpoint}_batch", duration_ms, success=False)

                logger.error(f"Request '{request_id}' failed: {e!s}")

        total_duration = (time.time() - self.start_time) * 1000
        logger.info(
            f"Batch '{self.name}' completed: {len(results)} requests in {total_duration:.0f}ms "
            f"(avg {total_duration/len(results):.0f}ms per request)",
        )

        return results

    def clear(self) -> None:
        """Clear all requests from the batch."""
        self.requests.clear()
        logger.debug(f"Cleared batch '{self.name}'")


def make_request_with_pooling(
    url: str, method: str = "GET", timeout: int = 10, **kwargs: object,
) -> requests.Response:
    """Make HTTP request using pooled session.

    Automatically uses connection pooling and configured retry strategy.

    :param url: URL to request
    :param method: HTTP method (GET, POST, etc.)
    :param timeout: Request timeout in seconds
    :param kwargs: Additional arguments to pass to requests
    :return: Response object
    """
    session = get_session()
    start_time = time.time()

    try:
        response = session.request(method, url, timeout=timeout, **kwargs)
        duration_ms = (time.time() - start_time) * 1000

        track_api_call(url, duration_ms, success=response.ok)

        logger.debug(f"Request to {url}: {response.status_code} ({duration_ms:.0f}ms)")

    except requests.exceptions.RequestException as e:
        duration_ms = (time.time() - start_time) * 1000
        track_api_call(url, duration_ms, success=False)

        logger.error(f"Request to {url} failed: {e!s}")

        raise
    else:
        return response


# Performance optimization metrics
def get_connection_pool_stats() -> dict[str, Any]:
    """Get statistics about the connection pool.

    :return: Dict with pool size, active connections, etc.
    """
    if _session is None:
        return {"status": "no_session"}

    pools = []
    for adapter in _session.adapters.values():
        if isinstance(adapter, HTTPAdapter):
            pool = adapter.poolmanager
            if pool:
                pools.append(
                    {
                        "pools": len(pool.pools) if hasattr(pool, "pools") else 0,
                        "connections": sum(
                            len(p.pool) if hasattr(p, "pool") else 0 for p in pool.pools.values()
                        )
                        if hasattr(pool, "pools")
                        else 0,
                    },
                )

    return {
        "status": "active",
        "adapters": len(_session.adapters),
        "pools": pools if pools else "no_pools_active",
    }
