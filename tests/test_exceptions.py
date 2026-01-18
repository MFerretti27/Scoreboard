#!/usr/bin/env python3
# ruff: noqa: E402
"""Test exception hierarchy and error handling."""
from __future__ import annotations

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from helper_functions.exceptions import (
    APIError,
    ConfigurationError,
    DataFetchError,
    DataValidationError,
    NetworkError,
    ScoreboardError,
)

# Test counter
tests_passed = 0
tests_failed = 0


def run_test(test_func: callable, test_name: str) -> None:
    """Run a test and track results."""
    global tests_passed, tests_failed
    try:
        test_func()
        print(f"✓ {test_name}")
        tests_passed += 1
    except AssertionError as e:
        print(f"✗ {test_name}: {e}")
        tests_failed += 1
    except Exception as e:
        print(f"✗ {test_name}: Unexpected error: {e}")
        tests_failed += 1


# ===== Exception Hierarchy Tests (Actual Behavior) =====
def test_all_exceptions_inherit_scoreboard_exception() -> None:
    """Test all custom exceptions inherit from ScoreboardError."""
    exceptions = [
        NetworkError("test"),
        APIError("test"),
        DataValidationError("test"),
        ConfigurationError("test"),
        DataFetchError("test"),
    ]
    for exc in exceptions:
        assert isinstance(exc, ScoreboardError), f"{type(exc)} should inherit ScoreboardError"


def test_exception_catching_by_base_class() -> None:
    """Test catching exceptions by base ScoreboardError catches all types."""
    test_exceptions = [
        DataFetchError("Test error"),
        APIError("API failed"),
        NetworkError("Network unavailable"),
        DataValidationError("Invalid data"),
    ]
    for exc in test_exceptions:
        try:
            raise exc
        except ScoreboardError:
            pass  # Successfully caught as ScoreboardError
        except Exception:
            msg = f"{type(exc)} should be caught as ScoreboardError"
            raise AssertionError(msg) from None


def test_exception_catching_by_specific_type() -> None:
    """Test catching exceptions by specific type doesn't catch others."""
    # Should catch APIError
    try:
        raise APIError("API failed", status_code=500)
    except APIError:
        pass  # Success
    except Exception:
        raise AssertionError("Should have been caught as APIError") from None

    # Should NOT catch NetworkError as APIError
    try:
        raise NetworkError("Network unavailable")
    except APIError:
        raise AssertionError("NetworkError should not be caught as APIError") from None
    except NetworkError:
        pass  # Success


def test_recoverable_vs_non_recoverable() -> None:
    """Test recoverable flag affects behavior correctly."""
    recoverable = [
        NetworkError("test"),
        APIError("test"),
        DataValidationError("test"),
        DataFetchError("test"),
    ]
    non_recoverable = [
        ConfigurationError("test"),
        ScoreboardError("test"),
    ]

    for exc in recoverable:
        assert exc.recoverable is True, f"{type(exc).__name__} should be recoverable"

    for exc in non_recoverable:
        assert exc.recoverable is False, f"{type(exc).__name__} should NOT be recoverable"


def test_api_error_status_code_in_error_code() -> None:
    """Test APIError includes status code in error code when available."""
    exc_with_code = APIError("Error", status_code=429)
    assert "429" in exc_with_code.error_code, "Status code should be in error_code"

    exc_without_code = APIError("Error")
    assert "UNKNOWN" in exc_without_code.error_code, "Should have UNKNOWN when no status"


def test_data_fetch_error_league_in_error_code() -> None:
    """Test DataFetchError includes league in error code when available."""
    exc_with_league = DataFetchError("Error", league="NFL")
    assert "NFL" in exc_with_league.error_code, "League should be in error_code"

    exc_without_league = DataFetchError("Error")
    assert "UNKNOWN" in exc_without_league.error_code


def test_configuration_error_setting_in_error_code() -> None:
    """Test ConfigurationError includes setting name in error code when available."""
    exc_with_setting = ConfigurationError("Error", setting_name="RETRY_MAX_ATTEMPTS")
    assert "RETRY_MAX_ATTEMPTS" in exc_with_setting.error_code

    exc_without_setting = ConfigurationError("Error")
    assert "UNKNOWN" in exc_without_setting.error_code


if __name__ == "__main__":
    print("\n=== Running Exception Tests ===\n")

    run_test(test_all_exceptions_inherit_scoreboard_exception, "All exceptions inherit base")
    run_test(test_exception_catching_by_base_class, "Catching by base class")
    run_test(test_exception_catching_by_specific_type, "Catching by specific type")
    run_test(test_recoverable_vs_non_recoverable, "Recoverable flag behavior")
    run_test(test_api_error_status_code_in_error_code, "APIError status code encoding")
    run_test(test_data_fetch_error_league_in_error_code, "DataFetchError league encoding")
    run_test(test_configuration_error_setting_in_error_code, "ConfigError setting encoding")

    print(f"\n=== Exception Test Results ===")
    print(f"Passed: {tests_passed}")
    print(f"Failed: {tests_failed}")
    print(f"Total:  {tests_passed + tests_failed}\n")

    sys.exit(0 if tests_failed == 0 else 1)
