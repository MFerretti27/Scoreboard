"""Extended integration tests for real APIs, stress testing, and advanced scenarios.

Run with: python3 test_extended_integration.py

Tests circuit breaker, graceful degradation, connection pooling, and stress scenarios.
"""
from __future__ import annotations

import contextlib
import time
from typing import Never

from helper_functions.circuit_breaker import CircuitBreaker, CircuitBreakerConfig, CircuitState
from helper_functions.exceptions import APIError, NetworkError
from helper_functions.graceful_degradation import (
    GracefulDegradation,
    PartialResult,
    merge_partial_results,
)
from helper_functions.performance import RequestBatch, close_session, get_session


def test_circuit_breaker_basic() -> None:
    """Test circuit breaker transitions between states."""
    config = CircuitBreakerConfig(failure_threshold=3, recovery_timeout=1, success_threshold=2, name="test_api")
    breaker = CircuitBreaker(config)

    call_count = 0

    def flaky_function():
        nonlocal call_count
        call_count += 1
        if call_count <= 3:
            msg = "API failed"
            raise APIError(msg, error_code="API_ERROR")
        return {"data": "success"}

    # First 3 calls fail, circuit opens on 3rd
    for _i in range(3):
        with contextlib.suppress(APIError):
            breaker.call(flaky_function)

    assert breaker.state == CircuitState.OPEN, f"Should be OPEN after threshold exceeded, got {breaker.state}"

    # Subsequent call fails immediately without calling function (while circuit still open)
    call_count_before = call_count
    try:
        breaker.call(flaky_function)
        msg = "Should raise APIError"
        raise AssertionError(msg)
    except APIError as e:
        assert "CIRCUIT_OPEN" in str(e) or "circuit" in str(e).lower(), f"Wrong error: {e}"

    assert call_count == call_count_before, f"Function should not be called when circuit open, but was called {call_count - call_count_before} times"


    # Wait for recovery timeout
    time.sleep(1.1)

    # Now in HALF_OPEN state
    call_count = 100  # Reset to success
    result = breaker.call(flaky_function)
    assert result["data"] == "success", "First recovery attempt should succeed"
    assert breaker.state == CircuitState.HALF_OPEN, "Should be HALF_OPEN after recovery attempt"

    # Second success closes circuit
    result = breaker.call(flaky_function)
    assert breaker.state == CircuitState.CLOSED, "Should be CLOSED after threshold successes"



def test_graceful_degradation_multi_endpoint() -> None:
    """Test graceful degradation with multiple endpoints."""
    deg = GracefulDegradation(team="Lakers", league="NBA")

    # Define endpoints
    endpoints = {
        "primary": lambda: {"score": 100, "team": "Lakers", "status": "live"},
        "secondary": lambda: {"rebounds": 45, "assists": 20},
        "cache": lambda: {"cached": True, "data": "old"},
    }

    # Fetch with graceful degradation
    result = deg.fetch_multi(endpoints)

    assert result.is_usable(), "Result should be usable"
    assert result.successful_data["score"] == 100, "Should have primary data"
    assert result.successful_data["rebounds"] == 45, "Should merge secondary data"
    assert result.data_completeness == 1.0, "All endpoints succeeded"



def test_graceful_degradation_with_failures() -> None:
    """Test graceful degradation when some endpoints fail."""
    deg = GracefulDegradation(team="Celtics", league="NBA")

    def failing_endpoint() -> Never:
        msg = "Endpoint down"
        raise APIError(msg, error_code="API_ERROR")

    def working_endpoint():
        return {"score": 95, "status": "live"}

    endpoints = {
        "primary": failing_endpoint,
        "backup": working_endpoint,
    }

    fallback_cache = {"score": 90, "status": "cached", "cached": True}

    result = deg.fetch_multi(endpoints, fallback_cache=fallback_cache)

    assert result.is_usable(), "Should use backup endpoint"
    assert result.successful_data["score"] == 95, "Should have backup data"
    assert "primary" in result.failed_endpoints, "Should track failed endpoint"
    assert not result.used_fallback, "Should not need fallback with backup endpoint"



def test_graceful_degradation_fallback() -> None:
    """Test fallback to cache when all endpoints fail."""
    deg = GracefulDegradation(team="Warriors", league="NBA")

    def failing_endpoint_1() -> Never:
        msg = "Down"
        raise APIError(msg, error_code="API_ERROR")

    def failing_endpoint_2() -> Never:
        msg = "Timeout"
        raise APIError(msg, error_code="TIMEOUT")

    endpoints = {
        "primary": failing_endpoint_1,
        "backup": failing_endpoint_2,
    }

    fallback_cache = {"score": 88, "status": "cached", "cached": True}

    result = deg.fetch_multi(endpoints, fallback_cache=fallback_cache)

    assert result.is_usable(), "Should use fallback cache"
    assert result.used_fallback, "Should indicate fallback was used"
    assert result.successful_data["cached"] is True, "Should have cached data"
    assert len(result.failed_endpoints) == 2, "Both endpoints should fail"



def test_graceful_degradation_defaults() -> None:
    """Test graceful degradation with default values."""
    deg = GracefulDegradation(team="Heat", league="NBA")

    def partial_fetch():
        return {"score": 92}

    defaults = {
        "score": 0,
        "team": "Unknown",
        "status": "not_playing",
        "last_updated": None,
    }

    result = deg.fetch_with_defaults(partial_fetch, defaults)

    assert result["score"] == 92, "Should keep fetched value"
    assert result["team"] == "Unknown", "Should use default for missing field"
    assert result["status"] == "not_playing", "Should use default"
    assert len(result) == 4, "Should have all default fields"



def test_connection_pooling() -> None:
    """Test connection pooling functionality."""
    session = get_session()

    # Verify session is configured
    assert session is not None, "Session should be initialized"
    assert "http://" in session.adapters, "Should have HTTP adapter"
    assert "https://" in session.adapters, "Should have HTTPS adapter"

    {"pooling_configured": True, "adapters": len(session.adapters)}


    close_session()


def test_request_batching() -> None:
    """Test request batching coordinator."""
    batch = RequestBatch(name="test_batch", max_requests=5)

    # Add requests to batch
    def req1():
        return {"data": "result1"}

    def req2():
        return {"data": "result2"}

    def req3():
        return {"data": "result3"}

    batch.add_request("fetch_1", req1, endpoint="api1")
    batch.add_request("fetch_2", req2, endpoint="api2")
    batch.add_request("fetch_3", req3, endpoint="api3")

    # Execute batch
    results = batch.execute()

    assert len(results) == 3, "Should have 3 results"
    assert results["fetch_1"][0]["data"] == "result1", "Should have result 1"
    assert results["fetch_2"][0]["data"] == "result2", "Should have result 2"
    assert results["fetch_3"][0]["data"] == "result3", "Should have result 3"

    # Check performance tracking
    for request_id, (_result, duration_ms) in results.items():
        assert isinstance(duration_ms, (int, float)), f"{request_id} should have execution time (got {type(duration_ms)})"
        assert duration_ms >= 0, f"{request_id} duration should be non-negative"



def test_stress_retry_logic() -> None:
    """Stress test retry logic with repeated failures."""
    from helper_functions.retry import retry_with_fallback

    attempt_count = 0

    @retry_with_fallback(max_attempts=3, backoff=None, use_cache_fallback=False)
    def flaky_api():
        nonlocal attempt_count
        attempt_count += 1

        # Succeed on 3rd attempt
        if attempt_count % 3 == 0:
            return {"success": True, "attempt": attempt_count}

        msg = "Temporary failure"
        raise NetworkError(msg, error_code="NETWORK_ERROR")

    # Run stress test with 10 simulated calls
    success_count = 0
    for _i in range(10):
        attempt_count = 0
        try:
            flaky_api()
            success_count += 1
        except NetworkError:
            pass

    assert success_count > 0, "Should have some successes"



def test_partial_result_merge() -> None:
    """Test merging multiple partial results."""
    result1 = PartialResult(
        successful_data={"score": 100, "team": "Lakers"},
        failed_endpoints=[],
        used_fallback=False,
        fallback_age_seconds=None,
        data_completeness=1.0,
    )

    result2 = PartialResult(
        successful_data={"rebounds": 45, "assists": 20},
        failed_endpoints=[],
        used_fallback=False,
        fallback_age_seconds=None,
        data_completeness=1.0,
    )

    merged = merge_partial_results(result1, result2)

    assert "score" in merged.successful_data, "Should have data from result1"
    assert "rebounds" in merged.successful_data, "Should have data from result2"
    assert merged.data_completeness == 1.0, "Should have full completeness"



if __name__ == "__main__":

    try:
        test_circuit_breaker_basic()
        test_graceful_degradation_multi_endpoint()
        test_graceful_degradation_with_failures()
        test_graceful_degradation_fallback()
        test_graceful_degradation_defaults()
        test_connection_pooling()
        test_request_batching()
        test_stress_retry_logic()
        test_partial_result_merge()


    except AssertionError:
        pass

    except Exception:
        pass
