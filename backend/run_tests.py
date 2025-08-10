#!/usr/bin/env python3
"""Test runner script for Finance Inbox Backend API."""

import sys
import subprocess
import argparse
from pathlib import Path

def run_command(cmd, description):
    """Run a command and print the result."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    result = subprocess.run(cmd, capture_output=False)
    if result.returncode != 0:
        print(f"❌ {description} failed with exit code {result.returncode}")
        return False
    else:
        print(f"✅ {description} completed successfully")
        return True

def main():
    parser = argparse.ArgumentParser(description="Run tests for Finance Inbox Backend API")
    parser.add_argument("--coverage", action="store_true", help="Run with coverage report")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--fast", action="store_true", help="Skip slow tests")
    parser.add_argument("--specific", "-s", help="Run specific test file or test function")
    parser.add_argument("--markers", "-m", help="Run tests with specific markers")
    parser.add_argument("--install-deps", action="store_true", help="Install test dependencies first")
    
    args = parser.parse_args()
    
    # Change to backend directory
    backend_dir = Path(__file__).parent
    print(f"Working directory: {backend_dir}")
    
    success = True
    
    # Install dependencies if requested
    if args.install_deps:
        if not run_command(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            "Installing dependencies"
        ):
            return 1
    
    # Build pytest command
    pytest_cmd = [sys.executable, "-m", "pytest"]
    
    # Add coverage if requested
    if args.coverage:
        pytest_cmd.extend(["--cov=apis", "--cov=services", "--cov=models", 
                          "--cov-report=term-missing", "--cov-report=html:htmlcov"])
    
    # Add verbosity
    if args.verbose:
        pytest_cmd.extend(["-v", "-s"])
    
    # Add specific test file/function
    if args.specific:
        pytest_cmd.append(args.specific)
    
    # Add markers
    if args.markers:
        pytest_cmd.extend(["-m", args.markers])
    
    # Skip slow tests if fast mode
    if args.fast:
        pytest_cmd.extend(["-m", "not slow"])
    
    # Add test directory
    if not args.specific:
        pytest_cmd.append("tests/")
    
    # Run tests
    if not run_command(pytest_cmd, "Running tests"):
        success = False
    
    # Generate coverage report if coverage was enabled
    if args.coverage and success:
        print(f"\n{'='*60}")
        print("Coverage report generated in htmlcov/index.html")
        print(f"{'='*60}")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 