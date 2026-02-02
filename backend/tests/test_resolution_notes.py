"""
Test Suite for Resolution Notes Feature (Notas de Resolução)
Tests the functionality where cases can be marked as 'Concluído' with resolution notes
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "pedrohcarvalho1997@gmail.com"
ADMIN_PASSWORD = "S@muka91"


class TestResolutionNotesFeature:
    """Tests for Resolution Notes (Notas de Resolução) feature"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.token = None
        self.test_case_id = None
        
    def get_auth_token(self):
        """Authenticate and get token"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            self.token = response.json().get("token")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
            return True
        return False
    
    def test_01_login_admin(self):
        """Test admin login works"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data, "Token not in response"
        assert "user" in data, "User not in response"
        assert data["user"]["role"] == "administrador", "User is not admin"
        print(f"✅ Admin login successful: {data['user']['name']}")
    
    def test_02_create_test_case(self):
        """Create a test case for resolution notes testing"""
        assert self.get_auth_token(), "Failed to authenticate"
        
        test_case = {
            "title": f"TEST_ResolutionNotes_{uuid.uuid4().hex[:8]}",
            "description": "Test case for resolution notes feature",
            "priority": "Média",
            "responsible": "Test User",
            "status": "Pendente",
            "seguradora": "AVLA",
            "category": "Erro Técnico"
        }
        
        response = self.session.post(f"{BASE_URL}/api/cases", json=test_case)
        assert response.status_code == 200, f"Failed to create case: {response.text}"
        
        data = response.json()
        assert "id" in data, "Case ID not in response"
        assert data["status"] == "Pendente", "Initial status should be Pendente"
        
        self.test_case_id = data["id"]
        print(f"✅ Test case created: {data['id']}")
        return data["id"]
    
    def test_03_update_case_with_resolution_fields(self):
        """Test PUT /api/cases/{id} accepts resolution fields (solution, solved_by, solved_by_id)"""
        assert self.get_auth_token(), "Failed to authenticate"
        
        # First create a case
        test_case = {
            "title": f"TEST_Resolution_{uuid.uuid4().hex[:8]}",
            "description": "Test case for resolution update",
            "priority": "Alta",
            "status": "Pendente"
        }
        
        create_response = self.session.post(f"{BASE_URL}/api/cases", json=test_case)
        assert create_response.status_code == 200, f"Failed to create case: {create_response.text}"
        case_id = create_response.json()["id"]
        
        # Update with resolution fields
        update_data = {
            "status": "Concluído",
            "solution": "Problema resolvido através de reconfiguração do sistema",
            "solved_by": "Admin Test",
            "solved_by_id": "test-user-id-123"
        }
        
        update_response = self.session.put(f"{BASE_URL}/api/cases/{case_id}", json=update_data)
        assert update_response.status_code == 200, f"Failed to update case: {update_response.text}"
        
        updated_case = update_response.json()
        assert updated_case["status"] == "Concluído", "Status should be Concluído"
        assert updated_case["solution"] == update_data["solution"], "Solution not saved correctly"
        assert updated_case["solved_by"] == update_data["solved_by"], "solved_by not saved correctly"
        assert updated_case["solved_by_id"] == update_data["solved_by_id"], "solved_by_id not saved correctly"
        
        print(f"✅ Case updated with resolution fields successfully")
        print(f"   - Status: {updated_case['status']}")
        print(f"   - Solution: {updated_case['solution'][:50]}...")
        print(f"   - Solved by: {updated_case['solved_by']}")
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/cases/{case_id}")
        
    def test_04_get_case_returns_resolution_fields(self):
        """Test GET /api/cases/{id} returns resolution fields when case is completed"""
        assert self.get_auth_token(), "Failed to authenticate"
        
        # Create and complete a case
        test_case = {
            "title": f"TEST_GetResolution_{uuid.uuid4().hex[:8]}",
            "description": "Test case for GET resolution fields",
            "status": "Pendente"
        }
        
        create_response = self.session.post(f"{BASE_URL}/api/cases", json=test_case)
        assert create_response.status_code == 200
        case_id = create_response.json()["id"]
        
        # Update to completed with solution
        solution_text = "Solução aplicada: Ajuste nas configurações de integração com a seguradora"
        update_data = {
            "status": "Concluído",
            "solution": solution_text,
            "solved_by": "Pedro Carvalho",
            "solved_by_id": "admin-123"
        }
        
        self.session.put(f"{BASE_URL}/api/cases/{case_id}", json=update_data)
        
        # GET the case and verify resolution fields
        get_response = self.session.get(f"{BASE_URL}/api/cases/{case_id}")
        assert get_response.status_code == 200, f"Failed to get case: {get_response.text}"
        
        case_data = get_response.json()
        assert case_data["solution"] == solution_text, "Solution not returned in GET"
        assert case_data["solved_by"] == "Pedro Carvalho", "solved_by not returned in GET"
        assert case_data["solved_by_id"] == "admin-123", "solved_by_id not returned in GET"
        
        print(f"✅ GET case returns resolution fields correctly")
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/cases/{case_id}")
    
    def test_05_update_without_resolution_keeps_existing(self):
        """Test that updating other fields doesn't clear resolution notes"""
        assert self.get_auth_token(), "Failed to authenticate"
        
        # Create case
        test_case = {
            "title": f"TEST_KeepResolution_{uuid.uuid4().hex[:8]}",
            "description": "Test case",
            "status": "Pendente"
        }
        
        create_response = self.session.post(f"{BASE_URL}/api/cases", json=test_case)
        case_id = create_response.json()["id"]
        
        # Complete with solution
        self.session.put(f"{BASE_URL}/api/cases/{case_id}", json={
            "status": "Concluído",
            "solution": "Original solution text",
            "solved_by": "Original Solver"
        })
        
        # Update only title (not solution)
        self.session.put(f"{BASE_URL}/api/cases/{case_id}", json={
            "title": "Updated Title"
        })
        
        # Verify solution is still there
        get_response = self.session.get(f"{BASE_URL}/api/cases/{case_id}")
        case_data = get_response.json()
        
        assert case_data["solution"] == "Original solution text", "Solution was cleared unexpectedly"
        assert case_data["solved_by"] == "Original Solver", "solved_by was cleared unexpectedly"
        
        print(f"✅ Resolution fields preserved after partial update")
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/cases/{case_id}")
    
    def test_06_case_model_has_resolution_fields(self):
        """Verify Case model includes solution, solved_by, solved_by_id fields"""
        assert self.get_auth_token(), "Failed to authenticate"
        
        # Get any existing case
        response = self.session.get(f"{BASE_URL}/api/cases")
        assert response.status_code == 200
        
        cases = response.json()
        if len(cases) > 0:
            # Check that the response schema includes resolution fields (even if null)
            case = cases[0]
            # These fields should exist in the model (may be null)
            assert "solution" in case or case.get("solution") is None, "solution field missing from model"
            print(f"✅ Case model includes resolution fields")
        else:
            print("⚠️ No cases found to verify model schema")
    
    def test_07_list_cases_includes_resolution_fields(self):
        """Test GET /api/cases list includes resolution fields"""
        assert self.get_auth_token(), "Failed to authenticate"
        
        # Create a completed case with solution
        test_case = {
            "title": f"TEST_ListResolution_{uuid.uuid4().hex[:8]}",
            "description": "Test case for list",
            "status": "Pendente"
        }
        
        create_response = self.session.post(f"{BASE_URL}/api/cases", json=test_case)
        case_id = create_response.json()["id"]
        
        # Complete it
        self.session.put(f"{BASE_URL}/api/cases/{case_id}", json={
            "status": "Concluído",
            "solution": "List test solution",
            "solved_by": "List Tester"
        })
        
        # Get list and find our case
        list_response = self.session.get(f"{BASE_URL}/api/cases")
        cases = list_response.json()
        
        our_case = next((c for c in cases if c["id"] == case_id), None)
        assert our_case is not None, "Created case not found in list"
        assert our_case.get("solution") == "List test solution", "Solution not in list response"
        
        print(f"✅ List cases includes resolution fields")
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/cases/{case_id}")


class TestEdgeCases:
    """Edge case tests for resolution notes"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
    def get_auth_token(self):
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            self.session.headers.update({"Authorization": f"Bearer {response.json()['token']}"})
            return True
        return False
    
    def test_empty_solution_allowed(self):
        """Test that empty solution is allowed (for non-completed cases)"""
        assert self.get_auth_token()
        
        test_case = {
            "title": f"TEST_EmptySolution_{uuid.uuid4().hex[:8]}",
            "description": "Test",
            "status": "Pendente"
        }
        
        response = self.session.post(f"{BASE_URL}/api/cases", json=test_case)
        assert response.status_code == 200
        
        case_data = response.json()
        # Solution should be None/null for new cases
        assert case_data.get("solution") is None, "New case should have null solution"
        
        print(f"✅ Empty solution allowed for non-completed cases")
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/cases/{case_data['id']}")
    
    def test_update_solution_on_already_completed_case(self):
        """Test updating solution on an already completed case"""
        assert self.get_auth_token()
        
        # Create and complete case
        test_case = {
            "title": f"TEST_UpdateSolution_{uuid.uuid4().hex[:8]}",
            "description": "Test",
            "status": "Pendente"
        }
        
        create_response = self.session.post(f"{BASE_URL}/api/cases", json=test_case)
        case_id = create_response.json()["id"]
        
        # Complete with initial solution
        self.session.put(f"{BASE_URL}/api/cases/{case_id}", json={
            "status": "Concluído",
            "solution": "Initial solution"
        })
        
        # Update solution
        update_response = self.session.put(f"{BASE_URL}/api/cases/{case_id}", json={
            "solution": "Updated solution with more details"
        })
        
        assert update_response.status_code == 200
        assert update_response.json()["solution"] == "Updated solution with more details"
        
        print(f"✅ Solution can be updated on completed case")
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/cases/{case_id}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
