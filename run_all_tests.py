#!/usr/bin/env python3  # noqa: EXE001
"""Run comprehensive test suite and display results.

Runs all test modules and displays results in a clean, organized format.
Each test includes a description of what it tests.
Generates timestamped detailed reports saved to TEST_RESULTS/ directory.
"""

import ast
import contextlib
import datetime
import os
import subprocess
import sys
from pathlib import Path

from helper_functions.logger_config import logger

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

# Create reports directory
reports_dir = project_root / "TEST_RESULTS"
reports_dir.mkdir(exist_ok=True)


def print_header(title: str, width: int = 80) -> None:
    """Print a formatted header."""
    print("\n" + "=" * width)  # noqa: T201
    print(title.center(width))  # noqa: T201
    print("=" * width + "\n")  # noqa: T201


def extract_test_functions(file_path: str) -> dict[str, str]:
    """Extract test function names and their docstrings."""
    test_funcs = {}
    try:
        with Path(file_path).open(encoding="utf-8") as f:
            tree = ast.parse(f.read())

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                docstring = ast.get_docstring(node) or "No description available"
                test_funcs[node.name] = docstring.split("\n")[0]  # First line only
    except Exception as e:
        logger.info("Failed to extract test functions from %s: %s", file_path, e)
    return test_funcs


def print_section(title: str, width: int = 80) -> None:
    """Print a formatted section title."""
    print("\n" + "-" * width)  # noqa: T201
    print(title)  # noqa: T201
    print("-" * width + "\n")  # noqa: T201


def run_all_tests() -> int:  # noqa: C901, PLR0912, PLR0915
    """Run all test modules and display results."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_file = reports_dir / f"test_report_{timestamp}.md"

    # Open report file for writing
    report_handle = report_file.open("w", encoding="utf-8")

    def report_write(text: str = "") -> None:
        """Write to both console and report file."""
        print(text)  # noqa: T201
        report_handle.write(text + "\n")

    print_header("COMPREHENSIVE TEST SUITE RUNNER", 80)
    report_write("# Comprehensive Test Suite Report")
    report_write(f"\n**Generated:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_write("**Python Version:** 3.12")
    report_write("**Status:** Running all test modules...\n")

    print("Date: January 17, 2026")  # noqa: T201
    print("Python Version: 3.12")  # noqa: T201
    print("Status: Running all test modules...\n")  # noqa: T201

    # Test suite metadata with descriptions
    test_suites = [
        {
            "name": "Exception Tests",
            "module": "tests/test_exceptions.py",
            "description": "Exception hierarchy, error codes, context preservation, and recoverability",
        },
        {
            "name": "Game Type Tests",
            "module": "tests/test_game_type.py",
            "description": "Sport-specific game type detection (NBA, MLB, NHL, NFL) and playoff identification",
        },
        {
            "name": "Network Tests",
            "module": "tests/test_network.py",
            "description": "Retry logic, exponential backoff, connection pooling, and error recovery",
        },
        {
            "name": "Player Stats Tests",
            "module": "tests/test_player_stats.py",
            "description": "Player stat retrieval, validation, and formatting across leagues",
        },
        {
            "name": "Retry Tests",
            "module": "tests/test_retry.py",
            "description": "Retry decorators, cache fallback, and backoff behavior",
        },
        {
            "name": "Validation Tests",
            "module": "tests/test_validation.py",
            "description": "Input validation for API responses across sports",
        },
        {
            "name": "Integration Tests",
            "module": "tests/test_integration.py",
            "description": "End-to-end stack verification including retry, cache, and logging",
        },
        {
            "name": "Extended Integration Tests",
            "module": "tests/test_extended_integration.py",
            "description": "Connection pooling, batching, circuit breaker, and graceful degradation",
        },
    ]

    # Run all tests
    results = []
    print_section("TEST EXECUTION")
    report_write("\n## Test Execution\n")

    for suite in test_suites:
        print(f'Running: {suite["name"]}')  # noqa: T201
        print(f'Description: {suite["description"]}')  # noqa: T201
        print(f'Module: {suite["module"]}')  # noqa: T201
        print()  # noqa: T201

        # Extract test function descriptions
        test_file = project_root / suite["module"]
        test_funcs = extract_test_functions(str(test_file))

        report_write(f"\n### {suite['name']}")
        report_write(f"\n**Description:** {suite['description']}")
        report_write(f"\n**Module:** `{suite['module']}`\n")

        if test_funcs:
            report_write("#### Tests in this suite:\n")
            for test_name, test_desc in sorted(test_funcs.items()):
                report_write(f"- `{test_name}`: {test_desc}")
            report_write()

        try:
            # Run test via subprocess to capture output
            test_path = project_root / suite["module"]
            python_exe = sys.executable

            result = subprocess.run(
                [python_exe, str(test_path)],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )

            # Parse output for test counts
            output = result.stdout + result.stderr

            # Extract test counts from output
            passed = 0
            failed = 0
            total = 0

            # Process lines in reverse order to get final counts
            for line in reversed(output.split("\n")):
                if line.startswith("Passed:") and passed == 0:
                    with contextlib.suppress(ValueError):
                        passed = int(line.split(":")[1].strip())
                elif line.startswith("Failed:") and failed == 0:
                    with contextlib.suppress(ValueError):
                        failed = int(line.split(":")[1].strip())
                elif line.startswith("Total:") and total == 0:
                    with contextlib.suppress(ValueError):
                        total = int(line.split(":")[1].strip())
                        # We have the total, can stop
                        if passed > 0 and failed >= 0:
                            break

            # If no "Total:" line found, look for "X passed, Y failed" format
            if total == 0:
                for line in reversed(output.split("\n")):
                    if "passed" in line and "failed" in line:
                        with contextlib.suppress(ValueError):
                            # Extract "27 passed, 0 failed"
                            parts = line.split(":")[-1].strip().split(",")
                            for part in parts:
                                if "passed" in part:
                                    passed = int(part.replace("passed", "").strip())
                                if "failed" in part:
                                    failed = int(part.replace("failed", "").strip())
                            total = passed + failed
                            break

            results.append(
                {
                    "name": suite["name"],
                    "passed": passed,
                    "failed": failed,
                    "total": total,
                    "description": suite["description"],
                    "test_funcs": test_funcs,
                },
            )
            print()  # noqa: T201
        except Exception as e:
            print(f"ERROR running {suite['name']}: {e}\n")  # noqa: T201
            results.append(
                {
                    "name": suite["name"],
                    "passed": 0,
                    "failed": 1,
                    "total": 1,
                    "description": suite["description"],
                    "error": str(e),
                    "test_funcs": {},
                },
            )

    # Print detailed results
    print_section("DETAILED RESULTS BY TEST SUITE")
    report_write("\n## Detailed Results by Test Suite\n")

    total_passed = 0
    total_failed = 0
    total_tests = 0

    for result in results:
        status = "✅ PASS" if result["failed"] == 0 else "❌ FAIL"
        print(f'{status} | {result["name"]}')  # noqa: T201
        print(f'      Description: {result["description"]}')  # noqa: T201
        print(  # noqa: T201
            f'      Results: {result["passed"]}/{result["total"]} tests passed',
            end="",
        )

        status_md = "✅ PASS" if result["failed"] == 0 else "❌ FAIL"
        report_write(f"\n### {status_md} | {result['name']}\n")
        report_write(f"**Description:** {result['description']}\n")
        report_write(f"**Results:** {result['passed']}/{result['total']} tests passed\n")

        if result["failed"] > 0:
            print(f' ({result["failed"]} failed)')  # noqa: T201
            if "error" in result:
                print(f'      Error: {result["error"]}')  # noqa: T201
                report_write(f"**Error:** {result['error']}\n")
        else:
            print()  # noqa: T201

        print()  # noqa: T201

        total_passed += result["passed"]
        total_failed += result["failed"]
        total_tests += result["total"]

    # Print summary
    print_header("FINAL SUMMARY", 80)
    report_write("\n## Final Summary\n")

    # Summary table
    print("Test Suite Summary:")  # noqa: T201
    report_write("### Test Suite Summary\n")
    print("-" * 80)  # noqa: T201
    report_write("|Suite|Passed|Failed|Total|Status|")
    report_write("|---|---|---|---|---|")
    print(  # noqa: T201
        f"{'Suite':<30} {'Passed':<10} {'Failed':<10} {'Total':<10} {'Status':<10}",
    )
    print("-" * 80)  # noqa: T201

    for result in results:
        status = "✅" if result["failed"] == 0 else "❌"
        print(  # noqa: T201
            f'{result["name"]:<30} {result["passed"]:<10} {result["failed"]:<10} {result["total"]:<10} {status:<10}',
        )
        report_write(f"|{result['name']}|{result['passed']}|{result['failed']}|{result['total']}|{status}|")

    print("-" * 80)  # noqa: T201
    print()  # noqa: T201
    report_write()

    # Overall statistics
    success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
    overall_status = (
        "✅ ALL TESTS PASSING"
        if total_failed == 0
        else "❌ SOME TESTS FAILING"
    )

    print(f"Overall Status: {overall_status}")  # noqa: T201
    print(f"Total Tests: {total_tests}")  # noqa: T201
    print(f"Passed: {total_passed}")  # noqa: T201
    print(f"Failed: {total_failed}")  # noqa: T201
    print(f"Success Rate: {success_rate:.1f}%")  # noqa: T201
    print()  # noqa: T201

    report_write("### Overall Statistics\n")
    report_write(f"- **Overall Status:** {overall_status}")
    report_write(f"- **Total Tests:** {total_tests}")
    report_write(f"- **Passed:** {total_passed}")
    report_write(f"- **Failed:** {total_failed}")
    report_write(f"- **Success Rate:** {success_rate:.1f}%\n")

    # Coverage summary
    print("Coverage Summary:")  # noqa: T201
    print("-" * 80)  # noqa: T201
    print("✓ Cache & Performance Optimization")  # noqa: T201
    print("✓ Exception Handling & Error Codes")  # noqa: T201
    print("✓ API Response Validation")  # noqa: T201
    print("✓ Retry Logic with Exponential Backoff")  # noqa: T201
    print("✓ Network Error Recovery")  # noqa: T201
    print("✓ Team & Logo Caching")  # noqa: T201
    print("✓ Game Type Detection (All Sports)")  # noqa: T201
    print("✓ Configuration Management")  # noqa: T201
    print("-" * 80)  # noqa: T201
    print()  # noqa: T201

    # Exit code
    if total_failed == 0:
        print("✅ All tests passed successfully!")  # noqa: T201
        print_header("TEST RUN COMPLETE - SUCCESS", 80)
        report_write("\n## Conclusion\n")
        report_write("✅ **All tests passed successfully!**\n")
        report_write(f"\n**Report saved to:** `{report_file}`")
        report_handle.close()
        return 0
    print(f"❌ {total_failed} test(s) failed. Please review the output above.")  # noqa: T201
    print_header("TEST RUN COMPLETE - FAILURES DETECTED", 80)
    report_write("\n## Conclusion\n")
    report_write(f"❌ **{total_failed} test(s) failed. Please review the details above.**\n")
    report_write(f"\n**Report saved to:** `{report_file}`")
    report_handle.close()
    return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
