"""Test network and API error handling scenarios."""
# ruff: noqa: E402

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from helper_functions.exceptions import APIError, NetworkError


def run_test(test_name: str, test_func) -> bool:
    """Run a single test and report result."""
    try:
        test_func()
    except AssertionError as e:
        print(f"✗ {test_name}: {e}")
        return False
    except Exception as e:
        print(f"✗ {test_name}: Unexpected error - {e}")
        return False
    else:
        print(f"✓ {test_name}")
        return True


# NetworkError Tests


def test_network_error_with_status() -> None:
    """Test NetworkError with custom error code."""
    error = NetworkError("Server error", error_code="SERVER_ERROR")
    assert error.error_code == "SERVER_ERROR"
    assert str(error) == "Server error"


def test_network_error_dns_failure() -> None:
    """Test NetworkError for DNS failure."""
    error = NetworkError("DNS lookup failed")
    assert "DNS" in str(error)
    assert error.recoverable is True


def test_network_error_connection_refused() -> None:
    """Test NetworkError for connection refused."""
    error = NetworkError("Connection refused", error_code="CONN_REFUSED")
    assert error.error_code == "CONN_REFUSED"
    assert error.recoverable is True


# APIError Tests


def test_api_error_invalid_response() -> None:
    """Test APIError for invalid response."""
    error = APIError("Invalid JSON response", error_code="INVALID_RESPONSE")
    assert error.error_code == "INVALID_RESPONSE"
    assert error.recoverable is True


def test_api_error_rate_limit() -> None:
    """Test APIError for rate limiting."""
    error = APIError("Rate limit exceeded", error_code="RATE_LIMIT", status_code=429)
    assert error.status_code == 429
    assert error.error_code == "RATE_LIMIT"
    assert error.recoverable is True


def test_api_error_server_error() -> None:
    """Test APIError for server error."""
    error = APIError("Internal server error", error_code="SERVER_ERROR", status_code=500)
    assert error.status_code == 500
    assert error.recoverable is True


def test_api_error_bad_gateway() -> None:
    """Test APIError for bad gateway."""
    error = APIError("Bad gateway", error_code="BAD_GATEWAY", status_code=502)
    assert error.status_code == 502
    assert error.recoverable is True


def test_api_error_service_unavailable() -> None:
    """Test APIError for service unavailable."""
    error = APIError("Service unavailable", error_code="SERVICE_UNAVAILABLE", status_code=503)
    assert error.status_code == 503
    assert error.recoverable is True


# Status Code Range Tests


def test_api_error_4xx_client_errors() -> None:
    """Test APIError for various 4xx client errors."""
    for code in [400, 403, 405, 409, 410]:
        error = APIError(f"Client error {code}", error_code="CLIENT_ERROR", status_code=code)
        assert error.status_code == code
        # APIError is recoverable by default
        assert error.recoverable is True


def test_api_error_5xx_server_errors() -> None:
    """Test APIError handles various 5xx server errors correctly."""
    for code in [500, 502, 503, 504]:
        error = APIError(f"Server error {code}", error_code="SERVER_ERROR", status_code=code)
        assert error.status_code == code
        # Server errors are typically recoverable
        assert error.recoverable is True


# Error Code Tests


def test_api_error_error_code() -> None:
    """Test APIError has correct error_code."""
    error = APIError("API failed", error_code="API_ERROR")
    assert error.error_code == "API_ERROR"


def test_network_error_error_code() -> None:
    """Test NetworkError has correct error_code."""
    error = NetworkError("Connection failed", error_code="NET_ERROR")
    assert error.error_code == "NET_ERROR"


def test_api_error_default_error_code() -> None:
    """Test APIError default error code with status."""
    error = APIError("Test", status_code=500)
    assert "500" in error.error_code or error.error_code.startswith("API_")


# Recoverable Flag Tests


def test_api_error_recoverable() -> None:
    """Test APIError is recoverable by default."""
    error = APIError("Temporary failure", error_code="TEMP")
    assert error.recoverable is True


def test_network_error_recoverable() -> None:
    """Test NetworkError is recoverable by default."""
    error = NetworkError("Network issue")
    assert error.recoverable is True


# Inheritance Tests


def test_api_error_is_network_error() -> None:
    """Test that APIError inherits from ScoreboardError."""
    from helper_functions.exceptions import ScoreboardError
    error = APIError("Test", error_code="TEST")
    # APIError should inherit from ScoreboardError
    assert isinstance(error, ScoreboardError), "APIError should be instance of ScoreboardError"
    # Check that it has expected properties
    assert hasattr(error, "error_code")
    assert hasattr(error, "recoverable")


def test_network_error_attributes() -> None:
    """Test NetworkError has expected attributes."""
    error = NetworkError("Test", error_code="TEST")
    assert hasattr(error, "error_code")
    assert hasattr(error, "recoverable")
    assert hasattr(error, "message")


def test_api_error_attributes() -> None:
    """Test APIError has all expected attributes."""
    error = APIError("Test", error_code="TEST", status_code=500)
    assert hasattr(error, "error_code")
    assert hasattr(error, "status_code")
    assert hasattr(error, "recoverable")
    assert hasattr(error, "message")


# Edge Cases


def test_network_error_default_code() -> None:
    """Test NetworkError with default error code."""
    error = NetworkError("No code provided")
    # Should use default code
    assert error.error_code == "NET_UNREACHABLE"


# Main Test Runner


def main() -> None:
    """Run all network error tests."""
    print("\n=== Network & API Error Tests ===\n")

    tests = [
        ("NetworkError with status code", test_network_error_with_status),
        ("NetworkError DNS failure", test_network_error_dns_failure),
        ("NetworkError connection refused", test_network_error_connection_refused),
        ("APIError invalid response", test_api_error_invalid_response),
        ("APIError rate limit", test_api_error_rate_limit),
        ("APIError server error", test_api_error_server_error),
        ("APIError bad gateway", test_api_error_bad_gateway),
        ("APIError service unavailable", test_api_error_service_unavailable),
        ("APIError 4xx client errors", test_api_error_4xx_client_errors),
        ("APIError 5xx server errors", test_api_error_5xx_server_errors),
        ("APIError error code", test_api_error_error_code),
        ("NetworkError error code", test_network_error_error_code),
        ("APIError default error code", test_api_error_default_error_code),
        ("APIError recoverable", test_api_error_recoverable),
        ("NetworkError recoverable", test_network_error_recoverable),
        ("APIError inheritance", test_api_error_is_network_error),
        ("NetworkError attributes", test_network_error_attributes),
        ("APIError attributes", test_api_error_attributes),
        ("NetworkError default code", test_network_error_default_code),
    ]

    tests_passed = 0
    tests_failed = 0

    for test_name, test_func in tests:
        if run_test(test_name, test_func):
            tests_passed += 1
        else:
            tests_failed += 1

    print(f"\n{'='*50}")
    print(f"Network Tests: {tests_passed} passed, {tests_failed} failed")
    print(f"{'='*50}\n")

    if tests_failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
