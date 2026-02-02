"""
Test suite for Pagination and Attachments features
Safe2Go Helpdesk - Iteration 2
"""
import pytest
import requests
import os
import tempfile

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "pedrohcarvalho1997@gmail.com"
TEST_PASSWORD = "S@muka91"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for tests"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["token"]


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Get headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestPaginationAPI:
    """Tests for pagination functionality on /api/cases endpoint"""
    
    def test_pagination_returns_correct_structure(self, auth_headers):
        """Test that pagination returns correct response structure"""
        response = requests.get(
            f"{BASE_URL}/api/cases?page=1&per_page=10",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "cases" in data, "Response should contain 'cases' key"
        assert "pagination" in data, "Response should contain 'pagination' key"
        
        pagination = data["pagination"]
        assert "page" in pagination
        assert "per_page" in pagination
        assert "total" in pagination
        assert "total_pages" in pagination
    
    def test_pagination_page_1_per_page_5(self, auth_headers):
        """Test pagination with page=1 and per_page=5"""
        response = requests.get(
            f"{BASE_URL}/api/cases?page=1&per_page=5",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["cases"]) <= 5, "Should return at most 5 cases"
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["per_page"] == 5
    
    def test_pagination_page_2_per_page_10(self, auth_headers):
        """Test pagination with page=2 and per_page=10"""
        response = requests.get(
            f"{BASE_URL}/api/cases?page=2&per_page=10",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["cases"]) <= 10, "Should return at most 10 cases"
        assert data["pagination"]["page"] == 2
        assert data["pagination"]["per_page"] == 10
    
    def test_pagination_total_pages_calculation(self, auth_headers):
        """Test that total_pages is calculated correctly"""
        response = requests.get(
            f"{BASE_URL}/api/cases?page=1&per_page=5",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        pagination = data["pagination"]
        
        # Calculate expected total pages
        expected_total_pages = (pagination["total"] + pagination["per_page"] - 1) // pagination["per_page"]
        assert pagination["total_pages"] == expected_total_pages
    
    def test_pagination_without_params_returns_all(self, auth_headers):
        """Test that without pagination params, all cases are returned"""
        response = requests.get(
            f"{BASE_URL}/api/cases",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        # Without pagination, should return a list directly
        assert isinstance(data, list), "Without pagination, should return a list"
    
    def test_pagination_different_per_page_values(self, auth_headers):
        """Test pagination with different per_page values (5, 10, 20, 50)"""
        for per_page in [5, 10, 20, 50]:
            response = requests.get(
                f"{BASE_URL}/api/cases?page=1&per_page={per_page}",
                headers=auth_headers
            )
            assert response.status_code == 200
            
            data = response.json()
            assert len(data["cases"]) <= per_page, f"Should return at most {per_page} cases"
            assert data["pagination"]["per_page"] == per_page


class TestAttachmentsAPI:
    """Tests for file attachments functionality"""
    
    @pytest.fixture
    def test_case_id(self, auth_headers):
        """Get a case ID for testing attachments"""
        response = requests.get(
            f"{BASE_URL}/api/cases?page=1&per_page=1",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        return data["cases"][0]["id"]
    
    @pytest.fixture
    def test_file(self):
        """Create a temporary test file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test content for attachment upload")
            return f.name
    
    def test_upload_attachment_to_case(self, auth_headers, test_case_id, test_file):
        """Test uploading an attachment to a case"""
        with open(test_file, 'rb') as f:
            response = requests.post(
                f"{BASE_URL}/api/cases/{test_case_id}/attachments",
                headers=auth_headers,
                files={"file": ("test_upload.txt", f, "text/plain")}
            )
        
        assert response.status_code == 200, f"Upload failed: {response.text}"
        
        data = response.json()
        assert "id" in data
        assert "filename" in data
        assert "original_filename" in data
        assert "file_type" in data
        assert "file_size" in data
        assert "uploaded_by" in data
        assert "url" in data
        
        # Store attachment ID for cleanup
        self.uploaded_attachment_id = data["id"]
        self.test_case_id = test_case_id
    
    def test_attachment_appears_in_case(self, auth_headers, test_case_id, test_file):
        """Test that uploaded attachment appears in case details"""
        # First upload a file
        with open(test_file, 'rb') as f:
            upload_response = requests.post(
                f"{BASE_URL}/api/cases/{test_case_id}/attachments",
                headers=auth_headers,
                files={"file": ("test_verify.txt", f, "text/plain")}
            )
        assert upload_response.status_code == 200
        attachment_id = upload_response.json()["id"]
        
        # Get case details
        response = requests.get(
            f"{BASE_URL}/api/cases/{test_case_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "attachments" in data
        assert len(data["attachments"]) > 0
        
        # Find our attachment
        attachment_ids = [a["id"] for a in data["attachments"]]
        assert attachment_id in attachment_ids, "Uploaded attachment should be in case"
        
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/cases/{test_case_id}/attachments/{attachment_id}",
            headers=auth_headers
        )
    
    def test_download_attachment(self, auth_headers, test_case_id, test_file):
        """Test downloading an attachment"""
        # First upload a file
        with open(test_file, 'rb') as f:
            upload_response = requests.post(
                f"{BASE_URL}/api/cases/{test_case_id}/attachments",
                headers=auth_headers,
                files={"file": ("test_download.txt", f, "text/plain")}
            )
        assert upload_response.status_code == 200
        
        attachment_data = upload_response.json()
        attachment_url = attachment_data["url"]
        attachment_id = attachment_data["id"]
        
        # Download the file
        download_response = requests.get(f"{BASE_URL}{attachment_url}")
        assert download_response.status_code == 200, "Should be able to download attachment"
        
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/cases/{test_case_id}/attachments/{attachment_id}",
            headers=auth_headers
        )
    
    def test_delete_attachment(self, auth_headers, test_case_id, test_file):
        """Test deleting an attachment"""
        # First upload a file
        with open(test_file, 'rb') as f:
            upload_response = requests.post(
                f"{BASE_URL}/api/cases/{test_case_id}/attachments",
                headers=auth_headers,
                files={"file": ("test_delete.txt", f, "text/plain")}
            )
        assert upload_response.status_code == 200
        attachment_id = upload_response.json()["id"]
        
        # Delete the attachment
        delete_response = requests.delete(
            f"{BASE_URL}/api/cases/{test_case_id}/attachments/{attachment_id}",
            headers=auth_headers
        )
        assert delete_response.status_code == 200
        assert "removido" in delete_response.json().get("message", "").lower()
        
        # Verify it's gone
        case_response = requests.get(
            f"{BASE_URL}/api/cases/{test_case_id}",
            headers=auth_headers
        )
        assert case_response.status_code == 200
        
        attachment_ids = [a["id"] for a in case_response.json().get("attachments", [])]
        assert attachment_id not in attachment_ids, "Deleted attachment should not be in case"
    
    def test_upload_invalid_file_type(self, auth_headers, test_case_id):
        """Test that invalid file types are rejected"""
        # Create a file with invalid extension
        with tempfile.NamedTemporaryFile(mode='w', suffix='.exe', delete=False) as f:
            f.write("fake executable content")
            invalid_file = f.name
        
        with open(invalid_file, 'rb') as f:
            response = requests.post(
                f"{BASE_URL}/api/cases/{test_case_id}/attachments",
                headers=auth_headers,
                files={"file": ("malware.exe", f, "application/octet-stream")}
            )
        
        # Should be rejected
        assert response.status_code == 400, "Invalid file type should be rejected"
    
    def test_attachment_metadata(self, auth_headers, test_case_id, test_file):
        """Test that attachment metadata is correctly stored"""
        with open(test_file, 'rb') as f:
            response = requests.post(
                f"{BASE_URL}/api/cases/{test_case_id}/attachments",
                headers=auth_headers,
                files={"file": ("metadata_test.txt", f, "text/plain")}
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify metadata
        assert data["original_filename"] == "metadata_test.txt"
        assert data["file_type"] == "text/plain"
        assert data["file_size"] > 0
        assert data["uploaded_by"] is not None
        assert data["uploaded_at"] is not None
        assert data["url"].startswith("/api/uploads/")
        
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/cases/{test_case_id}/attachments/{data['id']}",
            headers=auth_headers
        )


class TestAttachmentFileTypes:
    """Tests for allowed file types"""
    
    @pytest.fixture
    def test_case_id(self, auth_headers):
        """Get a case ID for testing"""
        response = requests.get(
            f"{BASE_URL}/api/cases?page=1&per_page=1",
            headers=auth_headers
        )
        return response.json()["cases"][0]["id"]
    
    @pytest.mark.parametrize("extension,content_type", [
        (".txt", "text/plain"),
        (".pdf", "application/pdf"),
        (".png", "image/png"),
        (".jpg", "image/jpeg"),
        (".csv", "text/csv"),
    ])
    def test_allowed_file_types(self, auth_headers, test_case_id, extension, content_type):
        """Test that allowed file types can be uploaded"""
        with tempfile.NamedTemporaryFile(mode='w', suffix=extension, delete=False) as f:
            f.write("test content")
            test_file = f.name
        
        with open(test_file, 'rb') as f:
            response = requests.post(
                f"{BASE_URL}/api/cases/{test_case_id}/attachments",
                headers=auth_headers,
                files={"file": (f"test{extension}", f, content_type)}
            )
        
        assert response.status_code == 200, f"File type {extension} should be allowed"
        
        # Cleanup
        if response.status_code == 200:
            attachment_id = response.json()["id"]
            requests.delete(
                f"{BASE_URL}/api/cases/{test_case_id}/attachments/{attachment_id}",
                headers=auth_headers
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
