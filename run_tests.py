#!/usr/bin/env python3
"""
Test Runner Script for ADB-UTIL

Quick test execution with various options and reporting.
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description=""):
    """Run a command and report results."""
    print(f"\n🔄 {description}")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 60)
    
    try:
        result = subprocess.run(cmd, capture_output=False, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - SUCCESS")
        else:
            print(f"❌ {description} - FAILED (exit code: {result.returncode})")
        return result.returncode == 0
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False


def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(description="ADB-UTIL Test Runner")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--gui", action="store_true", help="Run GUI tests only")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--parallel", action="store_true", help="Run tests in parallel")
    parser.add_argument("--slow", action="store_true", help="Include slow tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--file", type=str, help="Run specific test file")
    parser.add_argument("--function", type=str, help="Run specific test function")
    
    args = parser.parse_args()
    
    # Build pytest command
    cmd = [sys.executable, "-m", "pytest"]
    
    # Test selection
    if args.unit:
        cmd.extend(["-m", "unit"])
        description = "Unit Tests"
    elif args.integration:
        cmd.extend(["-m", "integration"])
        description = "Integration Tests"
    elif args.gui:
        cmd.extend(["-m", "gui"])
        description = "GUI Tests"
    elif args.file:
        cmd.append(f"tests/{args.file}")
        description = f"Tests from {args.file}"
        if args.function:
            cmd[-1] += f"::{args.function}"
            description += f"::{args.function}"
    else:
        cmd.append("tests/")
        description = "All Tests"
    
    # Test execution options
    if args.verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")
    
    if args.parallel:
        cmd.extend(["-n", "auto"])
    
    if args.coverage:
        cmd.extend(["--cov=src", "--cov-report=html", "--cov-report=term-missing"])
    
    if args.slow:
        cmd.extend(["-m", "slow or performance"])
    else:
        cmd.extend(["-m", "not slow"])
    
    # Additional useful options
    cmd.extend([
        "--tb=short",
        "--strict-markers",
        "--disable-warnings"
    ])
    
    print("🚀 ADB-UTIL Test Runner")
    print("=" * 60)
    
    # Check if tests directory exists
    if not Path("tests").exists():
        print("❌ Tests directory not found! Please run from project root.")
        return 1
    
    # Run the tests
    success = run_command(cmd, description)
    
    if success:
        print("\n🎉 All tests completed successfully!")
        if args.coverage:
            print("\n📊 Coverage report generated in htmlcov/index.html")
        return 0
    else:
        print("\n💥 Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())