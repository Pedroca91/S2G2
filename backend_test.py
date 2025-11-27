import requests
import sys
import json
from datetime import datetime, timedelta
import uuid
import websocket
import threading
import time

class Safe2GoHelpdeskTester:
    def __init__(self, base_url="https://validacao-ponto.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.ws_url = f"wss://validacao-ponto.preview.emergentagent.com/ws"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        # Test credentials
        self.admin_credentials = {
            "email": "pedro.carvalho@safe2go.com.br",
            "password": "senha123"  # Will try admin123 if this fails
        }
        self.client_credentials = {
            "email": "cliente@teste.com", 
            "password": "senha123"  # Will try cliente123 if this fails
        }
        
        # Test data storage
        self.admin_token = None
        self.client_token = None
        self.admin_user = None
        self.client_user = None
        self.created_case_id = None
        self.created_comment_id = None
        self.created_notification_id = None
        self.ws_connection = None
        self.ws_messages = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "test": name,
            "status": "PASSED" if success else "FAILED",
            "details": details
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None, token=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        # Add authorization header if token provided
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            details = f"Status: {response.status_code}"
            
            if not success:
                details += f", Expected: {expected_status}"
                if response.text:
                    try:
                        error_data = response.json()
                        details += f", Error: {error_data.get('detail', response.text[:200])}"
                    except:
                        details += f", Response: {response.text[:200]}"
            
            self.log_test(name, success, details)
            
            try:
                return success, response.json() if response.text else {}
            except:
                return success, {}

        except Exception as e:
            self.log_test(name, False, f"Exception: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test root API endpoint"""
        return self.run_test("Root API Endpoint", "GET", "", 200)

    def test_dashboard_stats(self):
        """Test dashboard statistics"""
        success, response = self.run_test("Dashboard Stats", "GET", "dashboard/stats", 200)
        if success:
            required_fields = ['total_cases', 'completed_cases', 'pending_cases', 'completion_percentage']
            for field in required_fields:
                if field not in response:
                    self.log_test(f"Dashboard Stats - {field} field", False, f"Missing field: {field}")
                    return False
            self.log_test("Dashboard Stats - All fields present", True)
        return success

    def test_dashboard_charts(self):
        """Test dashboard charts data"""
        success, response = self.run_test("Dashboard Charts", "GET", "dashboard/charts", 200)
        if success and isinstance(response, list):
            if len(response) == 7:  # Should return 7 days of data
                self.log_test("Dashboard Charts - 7 days data", True)
                # Check first item structure
                if response and 'date' in response[0] and 'completed' in response[0] and 'pending' in response[0]:
                    self.log_test("Dashboard Charts - Data structure", True)
                else:
                    self.log_test("Dashboard Charts - Data structure", False, "Missing required fields")
            else:
                self.log_test("Dashboard Charts - 7 days data", False, f"Expected 7 days, got {len(response)}")
        return success

    def test_create_case(self):
        """Test creating a new case"""
        test_case = {
            "jira_id": f"TEST-{datetime.now().strftime('%H%M%S')}",
            "title": "Test Case for API Testing",
            "description": "This is a test case created by automated testing",
            "responsible": "Test User",
            "status": "Pendente"
        }
        
        success, response = self.run_test("Create Case", "POST", "cases", 201, test_case)
        if success and 'id' in response:
            self.created_case_id = response['id']
            self.log_test("Create Case - ID returned", True)
        return success

    def test_get_cases(self):
        """Test getting all cases"""
        return self.run_test("Get All Cases", "GET", "cases", 200)

    def test_get_case_by_id(self):
        """Test getting a specific case by ID"""
        if not self.created_case_id:
            self.log_test("Get Case by ID", False, "No case ID available")
            return False
        
        return self.run_test("Get Case by ID", "GET", f"cases/{self.created_case_id}", 200)

    def test_update_case(self):
        """Test updating a case"""
        if not self.created_case_id:
            self.log_test("Update Case", False, "No case ID available")
            return False
        
        update_data = {
            "title": "Updated Test Case Title",
            "status": "Concluído"
        }
        
        return self.run_test("Update Case", "PUT", f"cases/{self.created_case_id}", 200, update_data)

    def test_filter_cases_by_status(self):
        """Test filtering cases by status"""
        return self.run_test("Filter Cases by Status", "GET", "cases", 200, params={"status": "Pendente"})

    def test_filter_cases_by_responsible(self):
        """Test filtering cases by responsible"""
        return self.run_test("Filter Cases by Responsible", "GET", "cases", 200, params={"responsible": "Test User"})

    def test_create_activity(self):
        """Test creating a new activity"""
        test_activity = {
            "responsible": "Test User",
            "activity": "Testing API endpoints",
            "case_id": self.created_case_id,
            "notes": "Automated test activity",
            "is_current": True
        }
        
        success, response = self.run_test("Create Activity", "POST", "activities", 201, test_activity)
        if success and 'id' in response:
            self.created_activity_id = response['id']
            self.log_test("Create Activity - ID returned", True)
        return success

    def test_get_activities(self):
        """Test getting all activities"""
        return self.run_test("Get All Activities", "GET", "activities", 200)

    def test_get_current_activities(self):
        """Test getting current activities"""
        return self.run_test("Get Current Activities", "GET", "activities/current", 200)

    def test_stop_activity(self):
        """Test stopping an activity"""
        if not self.created_activity_id:
            self.log_test("Stop Activity", False, "No activity ID available")
            return False
        
        return self.run_test("Stop Activity", "PUT", f"activities/{self.created_activity_id}/stop", 200)

    def test_delete_case(self):
        """Test deleting a case (cleanup)"""
        if not self.created_case_id:
            self.log_test("Delete Case", False, "No case ID available")
            return False
        
        return self.run_test("Delete Case", "DELETE", f"cases/{self.created_case_id}", 200)

    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Support System Backend API Tests")
        print(f"Testing against: {self.api_url}")
        print("=" * 60)
        
        # Basic API tests
        self.test_root_endpoint()
        
        # Dashboard tests
        self.test_dashboard_stats()
        self.test_dashboard_charts()
        
        # Cases CRUD tests
        self.test_create_case()
        self.test_get_cases()
        self.test_get_case_by_id()
        self.test_update_case()
        
        # Cases filtering tests
        self.test_filter_cases_by_status()
        self.test_filter_cases_by_responsible()
        
        # Activities tests
        self.test_create_activity()
        self.test_get_activities()
        self.test_get_current_activities()
        self.test_stop_activity()
        
        # Cleanup
        self.test_delete_case()
        
        # Print summary
        print("=" * 60)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        return self.tests_passed == self.tests_run

def main():
    tester = SupportSystemTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())