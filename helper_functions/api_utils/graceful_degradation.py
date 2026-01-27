"""Graceful degradation for handling partial API failures.

Allows the application to continue functioning with reduced data when some endpoints fail,
rather than completely failing on any single endpoint error.

Strategies:
- Fetch what you can: Get available data from successful endpoints
- Fallback to cached data: Use old cached data when fresh data unavailable
- Partial results: Return incomplete team data rather than nothing
- Default values: Provide sensible defaults for missing fields
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from helper_functions.logging.logger_config import logger

if TYPE_CHECKING:
    from collections.abc import Callable


@dataclass
class PartialResult:
    """Result of a gracefully degraded operation.

    Indicates what data was successfully fetched and what failed.
    """

    successful_data: dict[str, Any]  # Data that was successfully fetched
    failed_endpoints: list[str]  # Endpoints that failed
    used_fallback: bool  # Whether fallback data was used
    fallback_age_seconds: int | None  # Age of fallback data if used
    data_completeness: float  # 0.0-1.0 indicating how complete the result is

    def is_usable(self) -> bool:
        """Check if partial result has meaningful data.

        :return: True if at least some data was retrieved
        """
        return len(self.successful_data) > 0 or self.used_fallback

    def get_summary(self) -> str:
        """Get human-readable summary of result.

        :return: Summary string describing what succeeded/failed
        """
        parts = []

        if self.used_fallback:
            parts.append(f"(using fallback from {self.fallback_age_seconds}s ago)")

        if self.failed_endpoints:
            parts.append(f"Failed: {', '.join(self.failed_endpoints)}")

        completeness_pct = int(self.data_completeness * 100)
        parts.append(f"{completeness_pct}% complete")

        return " ".join(parts) if parts else "Complete"


class GracefulDegradation:
    """Coordinator for graceful degradation when endpoints fail.

    Fetches data from multiple sources and returns best available result
    even if some endpoints fail.

    Example:
        deg = GracefulDegradation(team="Lakers")
        result = deg.fetch_multi(
            endpoints={
                'espn': lambda: get_espn_data(team),
                'nba_api': lambda: get_nba_api_data(team),
                'cache': lambda: get_cached_data(team),
            },
            fallback_cache=cached_data,
        )
        if result.is_usable():
            use_data(result.successful_data)

    """

    def __init__(self, team: str = "unknown", league: str = "unknown") -> None:
        """Initialize graceful degradation coordinator.

        :param team: Team being fetched
        :param league: League (for context logging)
        """
        self.team = team
        self.league = league
        self.fetch_attempts: list[tuple[str, bool, str | None]] = []

    def fetch_multi(
        self,
        endpoints: dict[str, Callable[[], dict[str, Any]]],
        fallback_cache: dict[str, Any] | None = None,
        required_fields: list[str] | None = None,
    ) -> PartialResult:
        """Fetch from multiple endpoints with graceful degradation.

        Tries each endpoint in order. If all fail, uses fallback cache.

        :param endpoints: Dict of {endpoint_name: callable}
        :param fallback_cache: Cached data to use as last resort
        :param required_fields: Fields that must be present for usable result
        :return: PartialResult with best available data
        """
        successful_data: dict[str, Any] = {}
        failed_endpoints: list[str] = []
        used_fallback = False
        fallback_age = None

        required_fields = required_fields or []

        # Try each endpoint
        for endpoint_name, fetch_func in endpoints.items():
            try:
                logger.debug(f"Fetching from {endpoint_name} for {self.team}")
                data = fetch_func()

                if data and isinstance(data, dict):
                    successful_data.update(data)
                    self.fetch_attempts.append((endpoint_name, True, None))
                    logger.info(f"Successfully fetched from {endpoint_name}")
                else:
                    failed_endpoints.append(endpoint_name)
                    self.fetch_attempts.append((endpoint_name, False, "No data returned"))

            except Exception as e:
                failed_endpoints.append(endpoint_name)
                self.fetch_attempts.append((endpoint_name, False, str(e)))
                logger.warning(f"Failed to fetch from {endpoint_name}: {e!s}")

        # Check if we have required fields
        missing_fields = [f for f in required_fields if f not in successful_data]

        # Use fallback if primary fetch failed or missing required fields
        if (not successful_data or missing_fields) and fallback_cache:
            logger.warning(
                f"Using fallback cache for {self.team}: missing {missing_fields if missing_fields else 'all data'}",
            )
            successful_data = fallback_cache.copy()
            used_fallback = True
            fallback_age = 0  # Would be calculated from cache timestamp in real usage

        # Calculate data completeness
        if required_fields:
            available_fields = len([f for f in required_fields if f in successful_data])
            completeness = available_fields / len(required_fields)
        else:
            completeness = 1.0 if successful_data else 0.0

        return PartialResult(
            successful_data=successful_data,
            failed_endpoints=failed_endpoints,
            used_fallback=used_fallback,
            fallback_age_seconds=fallback_age,
            data_completeness=completeness,
        )

    def fetch_with_defaults(
        self,
        fetch_func: Callable[[], dict[str, Any]],
        defaults: dict[str, Any],
    ) -> dict[str, Any]:
        """Fetch data with defaults for missing fields.

        Useful for ensuring all expected fields exist even if fetch is incomplete.

        :param fetch_func: Function to fetch data
        :param defaults: Default values for missing fields
        :return: Data with defaults applied
        """
        try:
            data = fetch_func()
            if data is None:
                data = {}

            # Apply defaults for missing fields
            for key, default_value in defaults.items():
                if key not in data:
                    data[key] = default_value
                    logger.debug(f"Applied default for {key}: {default_value}")

        except Exception as e:
            logger.warning(f"Fetch failed for {self.team}, using all defaults: {e!s}")
            return defaults.copy()
        else:
            return data

    def get_report(self) -> str:
        """Get detailed report of fetch attempts.

        :return: Formatted report of what was tried and results
        """
        lines = [f"\n{'='*60}"]
        lines.append(f"Graceful Degradation Report: {self.team} ({self.league})")
        lines.append(f"{'='*60}")

        for endpoint, success, error in self.fetch_attempts:
            status = "✓ SUCCESS" if success else "✗ FAILED"
            error_msg = f": {error}" if error else ""
            lines.append(f"  {endpoint:<20} {status}{error_msg}")

        lines.append(f"{'='*60}\n")
        return "\n".join(lines)


def create_default_team_data(
    team_name: str = "Unknown",
    league: str = "Unknown",
) -> dict[str, Any]:
    """Create a default team data dict with sensible defaults.

    Used when all endpoint fetches fail and no cache available.

    :param team_name: Team name
    :param league: League name
    :return: Dict with default team data
    """
    return {
        "team_name": team_name,
        "league": league,
        "home_score": 0,
        "away_score": 0,
        "currently_playing": False,
        "data_available": False,
        "last_updated": None,
        "error": "Unable to fetch live data",
    }


def merge_partial_results(*results: PartialResult) -> PartialResult:
    """Merge multiple partial results into one.

    Combines data from multiple PartialResults, prioritizing earlier results.

    :param results: PartialResults to merge
    :return: Combined PartialResult
    """
    merged_data: dict[str, Any] = {}
    all_failed: list[str] = []
    any_fallback = False
    total_completeness = 0.0

    for result in results:
        # Don't overwrite existing data (first result wins)
        for key, value in result.successful_data.items():
            if key not in merged_data:
                merged_data[key] = value

        all_failed.extend(result.failed_endpoints)
        any_fallback = any_fallback or result.used_fallback
        total_completeness += result.data_completeness

    avg_completeness = total_completeness / len(results) if results else 0.0

    return PartialResult(
        successful_data=merged_data,
        failed_endpoints=list(set(all_failed)),  # Remove duplicates
        used_fallback=any_fallback,
        fallback_age_seconds=None,
        data_completeness=avg_completeness,
    )
