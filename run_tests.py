#!/usr/bin/env python3
"""
Test runner script for the refactored FastAPI application.
This script provides an easy way to run different types of tests.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle the output"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {cmd}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        if result.returncode == 0:
            print(f"✅ {description} completed successfully!")
        else:
            print(f"❌ {description} failed with return code {result.returncode}")
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error running {description}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Run tests for the refactored FastAPI application")
    parser.add_argument("--type", choices=["all", "service", "endpoint", "unit", "integration"], 
                       default="all", help="Type of tests to run")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--coverage", "-c", action="store_true", help="Run with coverage report")
    parser.add_argument("--file", "-f", help="Run specific test file")
    parser.add_argument("--test", "-t", help="Run specific test function")
    
    args = parser.parse_args()
    
    # Change to the project directory
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    print("🚀 FastAPI Refactored Tests Runner")
    print(f"Project root: {project_root}")
    print(f"Current directory: {os.getcwd()}")
    
    # Base pytest command
    pytest_cmd = "python -m pytest"
    
    # Add verbosity
    if args.verbose:
        pytest_cmd += " -v"
    else:
        pytest_cmd += " -q"
    
    # Add coverage if requested
    if args.coverage:
        pytest_cmd += " --cov=app --cov-report=html --cov-report=term-missing"
    
    # Determine what tests to run
    test_commands = []
    
    if args.file:
        # Run specific file
        test_file = f"app/auto_tests/{args.file}" if not args.file.startswith("app/auto_tests/") else args.file
        cmd = f"{pytest_cmd} {test_file}"
        if args.test:
            cmd += f"::{args.test}"
        test_commands.append((cmd, f"Running specific test: {args.file}"))
        
    elif args.test:
        # Run specific test across all files
        cmd = f"{pytest_cmd} -k {args.test}"
        test_commands.append((cmd, f"Running test pattern: {args.test}"))
        
    elif args.type == "service":
        # Run service layer tests
        test_commands.append((f"{pytest_cmd} app/auto_tests/test_services.py", "Service Layer Tests"))
        
    elif args.type == "endpoint":
        # Run all router tests
        test_commands.extend([
            (f"{pytest_cmd} app/auto_tests/test_router_application.py", "Application Router Tests"),
            (f"{pytest_cmd} app/auto_tests/test_router_device.py", "Device Router Tests"),
            (f"{pytest_cmd} app/auto_tests/test_router_users.py", "Users Router Tests"),
            (f"{pytest_cmd} app/auto_tests/test_router_signin.py", "Signin Router Tests"),
            (f"{pytest_cmd} app/auto_tests/test_router_general_property.py", "General Property Router Tests"),
            (f"{pytest_cmd} app/auto_tests/test_router_pipeline.py", "Pipeline Router Tests"),
            (f"{pytest_cmd} app/auto_tests/test_router_pipeline_input.py", "Pipeline Input Router Tests"),
            (f"{pytest_cmd} app/auto_tests/test_router_pipeline_session.py", "Pipeline Session Router Tests")
        ])
        
    elif args.type == "unit":
        # Run unit tests (marked with @pytest.mark.unit)
        test_commands.append((f"{pytest_cmd} -m unit app/auto_tests/", "Unit Tests"))
        
    elif args.type == "integration":
        # Run integration tests (marked with @pytest.mark.integration)
        test_commands.append((f"{pytest_cmd} -m integration app/auto_tests/", "Integration Tests"))
        
    else:  # args.type == "all"
        # Run all refactored tests
        test_commands.extend([
            (f"{pytest_cmd} app/auto_tests/test_services.py", "Service Layer Tests"),
            (f"{pytest_cmd} app/auto_tests/test_router_application.py", "Application Router Tests"),
            (f"{pytest_cmd} app/auto_tests/test_router_device.py", "Device Router Tests"),
            (f"{pytest_cmd} app/auto_tests/test_router_users.py", "Users Router Tests"),
            (f"{pytest_cmd} app/auto_tests/test_router_signin.py", "Signin Router Tests"),
            (f"{pytest_cmd} app/auto_tests/test_router_general_property.py", "General Property Router Tests"),
            (f"{pytest_cmd} app/auto_tests/test_router_pipeline.py", "Pipeline Router Tests"),
            (f"{pytest_cmd} app/auto_tests/test_router_pipeline_input.py", "Pipeline Input Router Tests"),
            (f"{pytest_cmd} app/auto_tests/test_router_pipeline_session.py", "Pipeline Session Router Tests")
        ])
    
    # Run the tests
    all_passed = True
    results = []
    
    for cmd, description in test_commands:
        success = run_command(cmd, description)
        results.append((description, success))
        if not success:
            all_passed = False
    
    # Print summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    for description, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status}: {description}")
    
    if all_passed:
        print(f"\n🎉 All tests passed successfully!")
        return 0
    else:
        print(f"\n💥 Some tests failed. Please check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
