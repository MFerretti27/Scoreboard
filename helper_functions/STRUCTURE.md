# Helper Functions Reorganization

## New Structure

The `helper_functions/` folder has been organized into 6 logical submodules:

```
helper_functions/
├── api_utils/
│   ├── cache.py                 # Caching layer
│   ├── circuit_breaker.py       # Circuit breaker pattern
│   ├── exceptions.py            # Custom exception classes
│   ├── graceful_degradation.py  # Graceful degradation strategies
│   ├── performance.py           # Performance optimization utilities
│   ├── recovery.py              # Failure recovery mechanisms
│   ├── retry.py                 # Retry with exponential backoff
│   └── validators.py            # Data validation functions
├── core/
│   └── handle_error.py          # Core error handling orchestration
├── data/
│   └── data_helpers.py          # Data processing utilities
├── logging/
│   └── logger_config.py         # Logging configuration & infrastructure
├── system/
│   ├── email.py                 # Email notifications
│   ├── internet_connection.py   # Network connectivity utilities
│   └── update.py                # Application updates & backups
└── ui/
    ├── main_menu_helpers.py     # Main menu UI utilities
    └── scoreboard_helpers.py    # Scoreboard GUI helpers
```

## Module Descriptions

| Module | Purpose | Contains |
|--------|---------|----------|
| **api_utils** | API operations & resilience | Caching, circuit breaker, retry logic, graceful degradation, validators, exceptions, recovery strategies |
| **core** | Error handling orchestration | `handle_error.py` - coordinates error responses across the app |
| **data** | Data processing | `data_helpers.py` - team matching, logo retrieval, doubleheader detection |
| **logging** | Logging infrastructure | `logger_config.py` - structured logging with context, metrics tracking |
| **system** | System operations | `email.py` - notifications, `update.py` - app updates & backups, `internet_connection.py` - network checks |
| **ui** | User interface helpers | `main_menu_helpers.py` - menu logic, `scoreboard_helpers.py` - GUI updates |

## Migration Notes

All imports have been automatically updated throughout the codebase:
- Updated in `get_data/` modules (ESPN, MLB, NBA, NHL data fetchers)
- Updated in `screens/` modules (main, scoreboard, clock screens)
- Updated in `gui_layouts/` modules
- Updated in `tests/` modules
- Updated in main application files (`main.py`, `settings.py`)

## Benefits

1. **Better Organization**: API-related resilience patterns consolidated in `api_utils`
2. **Reduced Folder Clutter**: 17 files organized into 6 subdirectories
3. **Clearer Dependencies**: Network operations now grouped with system utilities
4. **Easier Maintenance**: Logical grouping makes code navigation intuitive
5. **Scalability**: Easy to add new utilities to existing categories

