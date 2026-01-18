# Custom Error Handling & Recovery System

## Overview

The Scoreboard application now implements a comprehensive error handling and recovery system designed for production reliability. It includes custom exception classes, retry logic with exponential backoff, circuit breaker patterns, and fallback data caching.

## Components

### 1. Custom Exception Classes (`helper_functions/exceptions.py`)

All exceptions inherit from `ScoreboardException` with consistent error codes and recovery flags:

- **ScoreboardException**: Base class for all application errors
  - `message`: Human-readable error description
  - `error_code`: Machine-readable identifier (e.g., "NET_UNREACHABLE")
  - `recoverable`: Whether automatic recovery is possible

#### Specific Exception Types

- **NetworkError**: Network connectivity failures
  - Triggered by: Loss of internet connection, DNS failures
  - Recoverable: YES (with retry)
  - Example: `NetworkError("No internet connection", error_code="NET_DOWN")`

- **APIError**: API request failures
  - Triggered by: Timeouts, HTTP errors, rate limits, malformed responses
  - Recoverable: YES (with exponential backoff)
  - Includes HTTP status code for more precise error handling
  - Example: `APIError("API request timeout", status_code=408)`

- **DataValidationError**: Invalid or incomplete API responses
  - Triggered by: Missing required fields, invalid data format
  - Recoverable: YES (retry often fixes transient issues)
  - Tracks which fields are missing for debugging
  - Example: `DataValidationError("Missing home_score", missing_fields=["home_score"])`

- **ConfigurationError**: Invalid application configuration
  - Triggered by: Missing settings, invalid values, corrupted config files
  - Recoverable: NO (requires user intervention)
  - Example: `ConfigurationError("Invalid font setting", setting_name="FONT")`

- **DataFetchError**: Team/league data fetch failures
  - Triggered by: Specific team data unavailable, API returns no results
  - Recoverable: YES (with fallback mechanisms)
  - Tracks team and league for targeted recovery
  - Example: `DataFetchError("Could not fetch team data", team="Yankees", league="MLB")`

### 2. Recovery Strategies (`helper_functions/recovery.py`)

#### RetryConfig & RetryManager

Implements exponential backoff with jitter for API requests:

```python
from helper_functions.recovery import RetryManager, RetryConfig

# Create custom retry configuration
config = RetryConfig(
    max_attempts=3,
    initial_delay=1.0,      # Start with 1 second
    max_delay=30.0,         # Cap at 30 seconds
    exponential_base=2.0,   # Double delay each attempt
    jitter=True             # Add randomness to prevent thundering herd
)

manager = RetryManager(config)

# Execute function with automatic retry
result = manager.retry_with_backoff(api_fetch_function, team_name, league)
```

**How it works:**
- Attempt 1: Wait 1 second on failure
- Attempt 2: Wait 2 seconds on failure
- Attempt 3: Wait 4 seconds on failure
- Jitter prevents synchronized retries across multiple clients

**Delay Calculation:** `delay = min(initial_delay * (base ^ attempt), max_delay) ± 20%`

#### CircuitBreaker

Prevents cascading failures by stopping requests after repeated failures:

```python
from helper_functions.recovery import CircuitBreaker

breaker = CircuitBreaker(failure_threshold=5, timeout_seconds=300)

# Circuit opens after 5 failures, closes after 5 minutes
try:
    result = breaker.call(api_request_function)
except RuntimeError:
    print("Circuit breaker is open - service unavailable")
```

**States:**
- **Closed**: Normal operation, requests pass through
- **Open**: Too many failures, requests blocked for timeout period
- **Half-Open**: Timeout expired, attempting to recover with next request

#### FallbackDataProvider

Maintains cache of last successful response for use during outages:

```python
from helper_functions.recovery import FallbackDataProvider

provider = FallbackDataProvider()

# Cache successful data
provider.cache_data("Yankees", game_data)

# Retrieve cached data if less than 1 hour old
cached = provider.get_cached_data("Yankees", max_age_seconds=3600)

# Clear specific cache or all
provider.clear_cache("Yankees")  # Clear one
provider.clear_cache()            # Clear all
```

### 3. Updated Error Handler (`helper_functions/handle_error.py`)

The main error handler now uses all recovery mechanisms:

```python
from helper_functions.handle_error import handle_error

# Handle error with automatic recovery
handle_error(
    window=sg_window,
    error=exception_that_occurred,
    team_info=current_team_data
)
```

**Recovery Flow:**

1. **Classify Error**
   - Network error? → Reconnect
   - Recoverable error? → Retry with backoff
   - Permanent error? → Display clock with error

2. **Recovery Attempts** (if error is recoverable)
   - Use RetryManager for exponential backoff
   - Update UI with recovery progress
   - Cache successful data for fallback
   - Timeout after 12 attempts (~6 minutes)

3. **Network Recovery** (if connectivity lost)
   - Attempt reconnection
   - Check connectivity every 20 seconds
   - Display clock after 4 minutes offline
   - Log detailed error information

4. **Error Logging**
   - Comprehensive error details with context
   - Settings snapshot for debugging
   - Team information at time of failure
   - Stack traces for ScoreboardExceptions

## Usage Examples

### Example 1: API Fetch with Automatic Retry

```python
from helper_functions.recovery import RetryManager
from helper_functions.exceptions import APIError
from get_data.get_espn_data import get_espn_data

manager = RetryManager()

try:
    # This will automatically retry up to 3 times with backoff
    data = manager.retry_with_backoff(get_espn_data, team, team_info)
except APIError as e:
    logger.error(f"Failed after {e.error_code}: {e.message}")
```

### Example 2: Custom Data Fetch with Fallback

```python
from helper_functions.recovery import FallbackDataProvider
from helper_functions.exceptions import DataFetchError

provider = FallbackDataProvider()

try:
    data = fetch_team_data(team)
    provider.cache_data(team, data)
    return data
except DataFetchError:
    # Try fallback data from last successful fetch
    cached = provider.get_cached_data(team, max_age_seconds=3600)
    if cached:
        logger.warning(f"Using cached data for {team}")
        return cached
    raise
```

### Example 3: Preventing Cascading Failures

```python
from helper_functions.recovery import CircuitBreaker

breaker = CircuitBreaker(failure_threshold=5, timeout_seconds=300)

def fetch_with_protection():
    try:
        return breaker.call(external_api_call)
    except RuntimeError:
        logger.error("Service circuit breaker is open")
        return fallback_data()
```

## Error Handling Best Practices

### 1. Be Specific with Exceptions
```python
# ✓ Good - specific and recoverable
raise APIError("ESPN API timeout", status_code=408)

# ✗ Bad - generic exception
raise Exception("API failed")
```

### 2. Log Before Raising
```python
# ✓ Good - context is logged
logger.warning(f"API request for {team} failed: {response.status_code}")
raise APIError(f"API error for {team}", status_code=response.status_code)
```

### 3. Use Fallback Data
```python
# ✓ Good - graceful degradation
try:
    return fetch_fresh_data()
except DataFetchError:
    return provider.get_cached_data(key) or default_value
```

### 4. Classify Errors Before Handling
```python
# ✓ Good - appropriate recovery strategy
if isinstance(error, NetworkError):
    attempt_reconnect()
elif isinstance(error, APIError):
    retry_with_backoff()
else:
    display_error_and_exit()
```

## Configuration

Default retry configuration in `RetryManager`:
- **Max Attempts**: 3
- **Initial Delay**: 1 second
- **Max Delay**: 30 seconds
- **Exponential Base**: 2.0
- **Jitter**: Enabled (±20%)

Default circuit breaker configuration:
- **Failure Threshold**: 5 failures to open
- **Timeout**: 300 seconds before attempting reset

Adjust these in code as needed for your use case.

## Monitoring and Debugging

All recovery mechanisms log their actions:

```
DEBUG: Cached data for key: Yankees
WARNING: Attempt 1 failed: API timeout. Retrying in 2.3s...
INFO: Cached data for key: Yankees (age: 45s)
ERROR: Circuit breaker opened after 5 failures. Halting requests for 300s
```

Check logs for:
- Recovery attempt progress
- Cache hits/misses
- Circuit breaker status changes
- Error classification and recovery type

## Migration Guide

Existing code should be gradually updated to use custom exceptions:

```python
# Old code
except Exception as e:
    log_error(e)
    handle_error(window)

# New code
except APIError as e:
    logger.error(f"{e.error_code}: {e.message}")
    handle_error(window, error=e)
except NetworkError as e:
    logger.error(f"Network issue: {e.message}")
    handle_error(window, error=e)
```

## Testing Error Handling

To test error recovery:

```python
# Simulate network error
import unittest.mock
with unittest.mock.patch('helper_functions.internet_connection.is_connected', return_value=False):
    handle_error(window, error=NetworkError("Test network failure"))

# Simulate API error
with unittest.mock.patch('requests.get', side_effect=APIError("Test API failure", status_code=500)):
    manager = RetryManager()
    # This will retry 3 times then raise
```
