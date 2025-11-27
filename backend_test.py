import requests
import sys
import json
from datetime import datetime, timedelta
import uuid
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

    # ========== AUTHENTICATION TESTS ==========
    
    def test_admin_login(self):
        """Test admin login with pedro.carvalho@safe2go.com.br"""
        success, response = self.run_test("Admin Login", "POST", "auth/login", 200, self.admin_credentials)
        
        if not success:
            # Try alternative password
            alt_credentials = self.admin_credentials.copy()
            alt_credentials["password"] = "admin123"
            success, response = self.run_test("Admin Login (alt password)", "POST", "auth/login", 200, alt_credentials)
        
        if success and 'token' in response and 'user' in response:
            self.admin_token = response['token']
            self.admin_user = response['user']
            self.log_test("Admin Login - Token received", True)
            self.log_test("Admin Login - User data received", True)
            
            # Verify admin role
            if response['user'].get('role') == 'administrador':
                self.log_test("Admin Login - Role verification", True)
            else:
                self.log_test("Admin Login - Role verification", False, f"Expected 'administrador', got '{response['user'].get('role')}'")
        
        return success

    def test_client_login(self):
        """Test client login with cliente@teste.com"""
        success, response = self.run_test("Client Login", "POST", "auth/login", 200, self.client_credentials)
        
        if not success:
            # Try alternative password
            alt_credentials = self.client_credentials.copy()
            alt_credentials["password"] = "cliente123"
            success, response = self.run_test("Client Login (alt password)", "POST", "auth/login", 200, alt_credentials)
        
        if success and 'token' in response and 'user' in response:
            self.client_token = response['token']
            self.client_user = response['user']
            self.log_test("Client Login - Token received", True)
            self.log_test("Client Login - User data received", True)
            
            # Verify client role
            if response['user'].get('role') == 'cliente':
                self.log_test("Client Login - Role verification", True)
            else:
                self.log_test("Client Login - Role verification", False, f"Expected 'cliente', got '{response['user'].get('role')}'")
        
        return success

    def test_auth_me_admin(self):
        """Test /auth/me endpoint with admin token"""
        if not self.admin_token:
            self.log_test("Auth Me (Admin)", False, "No admin token available")
            return False
        
        success, response = self.run_test("Auth Me (Admin)", "GET", "auth/me", 200, token=self.admin_token)
        
        if success:
            if response.get('role') == 'administrador':
                self.log_test("Auth Me (Admin) - Role check", True)
            else:
                self.log_test("Auth Me (Admin) - Role check", False, f"Expected 'administrador', got '{response.get('role')}'")
        
        return success

    def test_auth_me_client(self):
        """Test /auth/me endpoint with client token"""
        if not self.client_token:
            self.log_test("Auth Me (Client)", False, "No client token available")
            return False
        
        success, response = self.run_test("Auth Me (Client)", "GET", "auth/me", 200, token=self.client_token)
        
        if success:
            if response.get('role') == 'cliente':
                self.log_test("Auth Me (Client) - Role check", True)
            else:
                self.log_test("Auth Me (Client) - Role check", False, f"Expected 'cliente', got '{response.get('role')}'")
        
        return success

    # ========== CASES TESTS ==========
    
    def test_get_cases_admin(self):
        """Test GET /cases as admin (should see all cases)"""
        if not self.admin_token:
            self.log_test("Get Cases (Admin)", False, "No admin token available")
            return False
        
        success, response = self.run_test("Get Cases (Admin)", "GET", "cases", 200, token=self.admin_token)
        
        if success and isinstance(response, list):
            self.log_test("Get Cases (Admin) - List returned", True)
            print(f"    Admin sees {len(response)} cases")
        
        return success

    def test_get_cases_client(self):
        """Test GET /cases as client (should see only own cases)"""
        if not self.client_token:
            self.log_test("Get Cases (Client)", False, "No client token available")
            return False
        
        success, response = self.run_test("Get Cases (Client)", "GET", "cases", 200, token=self.client_token)
        
        if success and isinstance(response, list):
            self.log_test("Get Cases (Client) - List returned", True)
            print(f"    Client sees {len(response)} cases")
            
            # Verify all cases belong to client
            if response:
                client_id = self.client_user.get('id') if self.client_user else None
                all_own_cases = all(case.get('creator_id') == client_id for case in response)
                if all_own_cases:
                    self.log_test("Get Cases (Client) - Role filtering", True)
                else:
                    self.log_test("Get Cases (Client) - Role filtering", False, "Client sees cases from other users")
        
        return success

    def test_create_case_client(self):
        """Test POST /cases as client"""
        if not self.client_token:
            self.log_test("Create Case (Client)", False, "No client token available")
            return False
        
        test_case = {
            "title": "Problema com sistema de pagamento",
            "description": "O sistema não está processando pagamentos via PIX corretamente. Erro 500 ao tentar finalizar transação.",
            "priority": "Alta",
            "seguradora": "AVLA",
            "category": "Erro Sistema"
        }
        
        success, response = self.run_test("Create Case (Client)", "POST", "cases", 200, test_case, token=self.client_token)
        
        if success and 'id' in response:
            self.created_case_id = response['id']
            self.log_test("Create Case (Client) - ID returned", True)
            
            # Verify creator_id is automatically set
            if response.get('creator_id') == self.client_user.get('id'):
                self.log_test("Create Case (Client) - Creator ID set", True)
            else:
                self.log_test("Create Case (Client) - Creator ID set", False, "Creator ID not set correctly")
        
        return success

    def test_get_case_by_id(self):
        """Test GET /cases/:id"""
        if not self.created_case_id:
            self.log_test("Get Case by ID", False, "No case ID available")
            return False
        
        success, response = self.run_test("Get Case by ID", "GET", f"cases/{self.created_case_id}", 200)
        
        if success:
            required_fields = ['id', 'title', 'description', 'status', 'creator_id']
            for field in required_fields:
                if field not in response:
                    self.log_test(f"Get Case by ID - {field} field", False, f"Missing field: {field}")
                    return False
            self.log_test("Get Case by ID - All fields present", True)
        
        return success

    # ========== COMMENTS TESTS ==========
    
    def test_create_public_comment(self):
        """Test POST /cases/:id/comments (public comment)"""
        if not self.created_case_id or not self.admin_token:
            self.log_test("Create Public Comment", False, "Missing case ID or admin token")
            return False
        
        comment_data = {
            "content": "Olá! Recebemos seu chamado e estamos analisando o problema. Em breve retornaremos com uma solução.",
            "is_internal": False
        }
        
        success, response = self.run_test("Create Public Comment", "POST", f"cases/{self.created_case_id}/comments", 200, comment_data, token=self.admin_token)
        
        if success and 'id' in response:
            self.created_comment_id = response['id']
            self.log_test("Create Public Comment - ID returned", True)
            
            # Verify comment properties
            if response.get('is_internal') == False:
                self.log_test("Create Public Comment - Public flag", True)
            else:
                self.log_test("Create Public Comment - Public flag", False, "Comment marked as internal")
        
        return success

    def test_create_internal_comment(self):
        """Test POST /cases/:id/comments with is_internal=true"""
        if not self.created_case_id or not self.admin_token:
            self.log_test("Create Internal Comment", False, "Missing case ID or admin token")
            return False
        
        comment_data = {
            "content": "INTERNO: Cliente relatou problema similar na semana passada. Verificar se é o mesmo bug do sistema de pagamento.",
            "is_internal": True
        }
        
        success, response = self.run_test("Create Internal Comment", "POST", f"cases/{self.created_case_id}/comments", 200, comment_data, token=self.admin_token)
        
        if success and 'id' in response:
            self.log_test("Create Internal Comment - ID returned", True)
            
            # Verify comment properties
            if response.get('is_internal') == True:
                self.log_test("Create Internal Comment - Internal flag", True)
            else:
                self.log_test("Create Internal Comment - Internal flag", False, "Comment not marked as internal")
        
        return success

    def test_get_comments_admin(self):
        """Test GET /cases/:id/comments as admin (should see all comments)"""
        if not self.created_case_id or not self.admin_token:
            self.log_test("Get Comments (Admin)", False, "Missing case ID or admin token")
            return False
        
        success, response = self.run_test("Get Comments (Admin)", "GET", f"cases/{self.created_case_id}/comments", 200, token=self.admin_token)
        
        if success and isinstance(response, list):
            self.log_test("Get Comments (Admin) - List returned", True)
            print(f"    Admin sees {len(response)} comments")
            
            # Check if internal comments are visible
            internal_comments = [c for c in response if c.get('is_internal') == True]
            if internal_comments:
                self.log_test("Get Comments (Admin) - Internal comments visible", True)
            else:
                self.log_test("Get Comments (Admin) - Internal comments visible", False, "No internal comments found")
        
        return success

    def test_get_comments_client(self):
        """Test GET /cases/:id/comments as client (should NOT see internal comments)"""
        if not self.created_case_id or not self.client_token:
            self.log_test("Get Comments (Client)", False, "Missing case ID or client token")
            return False
        
        success, response = self.run_test("Get Comments (Client)", "GET", f"cases/{self.created_case_id}/comments", 200, token=self.client_token)
        
        if success and isinstance(response, list):
            self.log_test("Get Comments (Client) - List returned", True)
            print(f"    Client sees {len(response)} comments")
            
            # Verify no internal comments are visible
            internal_comments = [c for c in response if c.get('is_internal') == True]
            if not internal_comments:
                self.log_test("Get Comments (Client) - Internal comments filtered", True)
            else:
                self.log_test("Get Comments (Client) - Internal comments filtered", False, f"Client sees {len(internal_comments)} internal comments")
        
        return success

    # ========== NOTIFICATIONS TESTS ==========
    
    def test_get_notifications_admin(self):
        """Test GET /notifications as admin"""
        if not self.admin_token:
            self.log_test("Get Notifications (Admin)", False, "No admin token available")
            return False
        
        success, response = self.run_test("Get Notifications (Admin)", "GET", "notifications", 200, token=self.admin_token)
        
        if success and isinstance(response, list):
            self.log_test("Get Notifications (Admin) - List returned", True)
            print(f"    Admin has {len(response)} notifications")
        
        return success

    def test_get_notifications_client(self):
        """Test GET /notifications as client"""
        if not self.client_token:
            self.log_test("Get Notifications (Client)", False, "No client token available")
            return False
        
        success, response = self.run_test("Get Notifications (Client)", "GET", "notifications", 200, token=self.client_token)
        
        if success and isinstance(response, list):
            self.log_test("Get Notifications (Client) - List returned", True)
            print(f"    Client has {len(response)} notifications")
            
            # Store a notification ID for testing mark as read
            if response:
                self.created_notification_id = response[0].get('id')
        
        return success

    def test_mark_notification_read(self):
        """Test POST /notifications/:id/read"""
        if not self.created_notification_id or not self.client_token:
            self.log_test("Mark Notification Read", False, "Missing notification ID or client token")
            return False
        
        success, response = self.run_test("Mark Notification Read", "POST", f"notifications/{self.created_notification_id}/read", 200, token=self.client_token)
        
        if success:
            self.log_test("Mark Notification Read - Success", True)
        
        return success

    def test_mark_all_notifications_read(self):
        """Test POST /notifications/mark-all-read"""
        if not self.client_token:
            self.log_test("Mark All Notifications Read", False, "No client token available")
            return False
        
        success, response = self.run_test("Mark All Notifications Read", "POST", "notifications/mark-all-read", 200, token=self.client_token)
        
        if success:
            self.log_test("Mark All Notifications Read - Success", True)
        
        return success

    # ========== USER MANAGEMENT TESTS (Admin only) ==========
    
    def test_get_all_users_admin(self):
        """Test GET /users as admin"""
        if not self.admin_token:
            self.log_test("Get All Users (Admin)", False, "No admin token available")
            return False
        
        success, response = self.run_test("Get All Users (Admin)", "GET", "users", 200, token=self.admin_token)
        
        if success and isinstance(response, list):
            self.log_test("Get All Users (Admin) - List returned", True)
            print(f"    System has {len(response)} users")
        
        return success

    def test_get_all_users_client_forbidden(self):
        """Test GET /users as client (should return 403)"""
        if not self.client_token:
            self.log_test("Get All Users (Client - Forbidden)", False, "No client token available")
            return False
        
        success, response = self.run_test("Get All Users (Client - Forbidden)", "GET", "users", 403, token=self.client_token)
        
        if success:
            self.log_test("Get All Users (Client) - Access denied correctly", True)
        
        return success

    def test_get_pending_users_admin(self):
        """Test GET /users/pending as admin"""
        if not self.admin_token:
            self.log_test("Get Pending Users (Admin)", False, "No admin token available")
            return False
        
        success, response = self.run_test("Get Pending Users (Admin)", "GET", "users/pending", 200, token=self.admin_token)
        
        if success and isinstance(response, list):
            self.log_test("Get Pending Users (Admin) - List returned", True)
            print(f"    System has {len(response)} pending users")
        
        return success

    def test_get_pending_users_client_forbidden(self):
        """Test GET /users/pending as client (should return 403)"""
        if not self.client_token:
            self.log_test("Get Pending Users (Client - Forbidden)", False, "No client token available")
            return False
        
        success, response = self.run_test("Get Pending Users (Client - Forbidden)", "GET", "users/pending", 403, token=self.client_token)
        
        if success:
            self.log_test("Get Pending Users (Client) - Access denied correctly", True)
        
        return success

    def run_all_tests(self):
        """Run all Safe2Go helpdesk backend tests"""
        print("🚀 Starting Safe2Go Helpdesk Backend API Tests")
        print(f"Testing against: {self.api_url}")
        print("=" * 70)
        
        # Basic API test
        self.test_root_endpoint()
        
        print("\n🔐 AUTHENTICATION TESTS")
        print("-" * 30)
        # Authentication tests
        self.test_admin_login()
        self.test_client_login()
        self.test_auth_me_admin()
        self.test_auth_me_client()
        
        print("\n📋 CASES TESTS")
        print("-" * 20)
        # Cases tests
        self.test_get_cases_admin()
        self.test_get_cases_client()
        self.test_create_case_client()
        self.test_get_case_by_id()
        
        print("\n💬 COMMENTS TESTS")
        print("-" * 25)
        # Comments tests
        self.test_create_public_comment()
        self.test_create_internal_comment()
        self.test_get_comments_admin()
        self.test_get_comments_client()
        
        print("\n🔔 NOTIFICATIONS TESTS")
        print("-" * 30)
        # Notifications tests
        self.test_get_notifications_admin()
        self.test_get_notifications_client()
        self.test_mark_notification_read()
        self.test_mark_all_notifications_read()
        
        print("\n👥 USER MANAGEMENT TESTS")
        print("-" * 35)
        # User management tests (admin only)
        self.test_get_all_users_admin()
        self.test_get_all_users_client_forbidden()
        self.test_get_pending_users_admin()
        self.test_get_pending_users_client_forbidden()
        
        # Print summary
        print("\n" + "=" * 70)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        # Print failed tests
        failed_tests = [result for result in self.test_results if result['status'] == 'FAILED']
        if failed_tests:
            print(f"\n❌ Failed Tests ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"   • {test['test']}: {test['details']}")
        
        return self.tests_passed == self.tests_run

def main():
    tester = Safe2GoHelpdeskTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())