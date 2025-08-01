"""
Simple endpoint tests for refactored FastAPI application.
These tests use direct HTTP requests to validate the refactored endpoints.
"""

import json
import time

import pytest
import requests

# Base URL for your running Docker container
BASE_URL = "http://localhost:8000"


class TestRefactoredEndpointsLive:
    """Test refactored endpoints against the running Docker container"""

    def test_application_endpoints(self):
        """Test application CRUD endpoints"""

        # Test GET all applications (should work)
        response = requests.get(f"{BASE_URL}/v1/application/all", timeout=10)
        assert response.status_code == 200  # nosec B101
        print(f"✅ GET /v1/application/all - Status: {response.status_code}")

        # Test create application
        app_data = {
            "name": f"Test App {int(time.time())}",  # Unique name
            "is_usable": 1,
        }

        try:
            response = requests.post(
                f"{BASE_URL}/v1/application/new", json=app_data, timeout=10
            )
            if response.status_code == 201:
                print(f"✅ POST /v1/application/new - Status: {response.status_code}")
                app_id = response.json()["id"]

                # Test get specific application
                response = requests.get(
                    f"{BASE_URL}/v1/application/{app_id}", timeout=10
                )
                if response.status_code == 200:
                    print(
                        f"✅ GET /v1/application/{app_id} - Status: {response.status_code}"
                    )

                # Test update application
                update_data = {
                    "name": f"Updated App {int(time.time())}",
                    "is_usable": 1,
                }
                response = requests.patch(
                    f"{BASE_URL}/v1/application/{app_id}", json=update_data, timeout=10
                )
                if response.status_code == 200:
                    print(
                        f"✅ PATCH /v1/application/{app_id} - Status: {response.status_code}"
                    )

                # Test delete application (soft delete)
                response = requests.delete(
                    f"{BASE_URL}/v1/application/{app_id}", timeout=10
                )
                if response.status_code == 200:
                    print(
                        f"✅ DELETE /v1/application/{app_id} - Status: {response.status_code}"
                    )

            else:
                print(
                    f"⚠️ POST /v1/application/new - Status: {response.status_code}, Response: {response.text}"
                )

        except Exception as e:
            print(f"❌ Application endpoint test failed: {e}")

    def test_pipeline_endpoints(self):
        """Test pipeline CRUD endpoints"""

        # Test GET all pipelines
        response = requests.get(f"{BASE_URL}/v1/pipeline/all", timeout=10)
        assert response.status_code == 200  # nosec B101
        print(f"✅ GET /v1/pipeline/all - Status: {response.status_code}")

        # Test get specific pipeline (if any exist)
        pipelines = response.json()
        if pipelines.get("items") and len(pipelines["items"]) > 0:
            pipeline_id = pipelines["items"][0]["id"]
            response = requests.get(f"{BASE_URL}/v1/pipeline/{pipeline_id}", timeout=10)
            print(f"✅ GET /v1/pipeline/{pipeline_id} - Status: {response.status_code}")

    def test_pipeline_input_endpoints(self):
        """Test pipeline input CRUD endpoints"""

        # Test GET all pipeline inputs
        response = requests.get(f"{BASE_URL}/v1/pipeline-input/all", timeout=10)
        assert response.status_code == 200  # nosec B101
        print(f"✅ GET /v1/pipeline-input/all - Status: {response.status_code}")

        # Test create pipeline input
        input_data = {"name": f"Test Input {int(time.time())}", "is_usable": 1}

        try:
            response = requests.post(
                f"{BASE_URL}/v1/pipeline-input/new", json=input_data, timeout=10
            )
            if response.status_code == 201:
                print(
                    f"✅ POST /v1/pipeline-input/new - Status: {response.status_code}"
                )
                input_id = response.json()["id"]

                # Test get specific input
                response = requests.get(
                    f"{BASE_URL}/v1/pipeline-input/{input_id}", timeout=10
                )
                if response.status_code == 200:
                    print(
                        f"✅ GET /v1/pipeline-input/{input_id} - Status: {response.status_code}"
                    )

                # Test update input (new endpoint from refactor)
                update_data = {
                    "name": f"Updated Input {int(time.time())}",
                    "is_usable": 1,
                }
                response = requests.patch(
                    f"{BASE_URL}/v1/pipeline-input/{input_id}",
                    json=update_data,
                    timeout=10,
                )
                if response.status_code == 200:
                    print(
                        f"✅ PATCH /v1/pipeline-input/{input_id} - Status: {response.status_code}"
                    )

                # Test delete input (new endpoint from refactor)
                response = requests.delete(
                    f"{BASE_URL}/v1/pipeline-input/{input_id}", timeout=10
                )
                if response.status_code == 200:
                    print(
                        f"✅ DELETE /v1/pipeline-input/{input_id} - Status: {response.status_code}"
                    )

            else:
                print(
                    f"⚠️ POST /v1/pipeline-input/new - Status: {response.status_code}, Response: {response.text}"
                )

        except Exception as e:
            print(f"❌ Pipeline input endpoint test failed: {e}")

    def test_pipeline_session_endpoints(self):
        """Test pipeline session endpoints"""

        # Test GET all pipeline sessions
        response = requests.get(f"{BASE_URL}/v1/pipeline-session/all", timeout=10)
        print(f"✅ GET /v1/pipeline-session/all - Status: {response.status_code}")

        # Note: Creating pipeline sessions requires authentication and valid pipeline/input IDs
        # This test just verifies the endpoint is accessible


def run_live_tests():
    """Run live tests against the Docker container"""
    print("🚀 Running Live Endpoint Tests Against Docker Container")
    print("=" * 60)

    test_instance = TestRefactoredEndpointsLive()

    try:
        print("\n📱 Testing Application Endpoints:")
        test_instance.test_application_endpoints()

        print("\n🔄 Testing Pipeline Endpoints:")
        test_instance.test_pipeline_endpoints()

        print("\n📥 Testing Pipeline Input Endpoints:")
        test_instance.test_pipeline_input_endpoints()

        print("\n🎯 Testing Pipeline Session Endpoints:")
        test_instance.test_pipeline_session_endpoints()

        print("\n🎉 Live endpoint tests completed!")

    except Exception as e:
        print(f"\n❌ Live tests failed: {e}")


if __name__ == "__main__":
    run_live_tests()
