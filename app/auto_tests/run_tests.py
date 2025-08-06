#!/usr/bin/env python3
"""
Test runner script for PolarisAI API Router Tests
Runs all router tests using SQLite database
"""

import os
import sys
import subprocess
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def run_tests():
    """Run all router tests"""
    test_directory = Path(__file__).parent
    
    # Test files to run
    test_files = [
        "test_router_application.py",
        "test_router_pipeline.py", 
        "test_router_device.py",
        "test_router_users.py",
        "test_router_pipeline_session.py",
        "test_router_general_property.py",
        "test_router_pipeline_input.py",
        "test_router_signin.py",
        "test_services.py"
    ]
    
    print("🚀 Running PolarisAI API Router Tests with SQLite")
    print("=" * 60)
    
    # Set environment variables for testing
    os.environ["TESTING"] = "1"
    os.environ["DATABASE_URL"] = "sqlite:///test.db"
    
    total_passed = 0
    total_failed = 0
    failed_files = []
    
    for test_file in test_files:
        test_path = test_directory / test_file
        if not test_path.exists():
            print(f"⚠️  Test file not found: {test_file}")
            continue
            
        print(f"\n📋 Running tests in {test_file}")
        print("-" * 40)
        
        try:
            # Run pytest for this specific file
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                str(test_path),
                "-v",
                "--tb=short",
                "--no-header"
            ], capture_output=True, text=True, cwd=project_root)
            
            if result.returncode == 0:
                print(f"✅ {test_file}: All tests passed")
                # Count passed tests from output
                passed_count = result.stdout.count(" PASSED")
                total_passed += passed_count
            else:
                print(f"❌ {test_file}: Some tests failed")
                failed_files.append(test_file)
                # Count failed tests from output
                failed_count = result.stdout.count(" FAILED")
                passed_count = result.stdout.count(" PASSED")
                total_failed += failed_count
                total_passed += passed_count
                
                # Show error details
                if result.stdout:
                    print("STDOUT:", result.stdout[-500:])  # Last 500 chars
                if result.stderr:
                    print("STDERR:", result.stderr[-500:])  # Last 500 chars
                    
        except Exception as e:
            print(f"💥 Error running {test_file}: {str(e)}")
            failed_files.append(test_file)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Total Passed: {total_passed}")
    print(f"❌ Total Failed: {total_failed}")
    print(f"📁 Files with failures: {len(failed_files)}")
    
    if failed_files:
        print("\nFailed files:")
        for file in failed_files:
            print(f"  - {file}")
    
    return len(failed_files) == 0

def run_specific_test(test_name):
    """Run a specific test file"""
    test_directory = Path(__file__).parent
    test_path = test_directory / f"test_router_{test_name}.py"
    
    if not test_path.exists():
        print(f"❌ Test file not found: test_router_{test_name}.py")
        return False
    
    print(f"🚀 Running specific test: {test_name}")
    print("=" * 60)
    
    # Set environment variables for testing
    os.environ["TESTING"] = "1"
    os.environ["DATABASE_URL"] = "sqlite:///test.db"
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            str(test_path),
            "-v",
            "--tb=long"
        ], cwd=project_root)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"💥 Error running test: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Run specific test
        test_name = sys.argv[1]
        success = run_specific_test(test_name)
    else:
        # Run all tests
        success = run_tests()
    
    sys.exit(0 if success else 1)
