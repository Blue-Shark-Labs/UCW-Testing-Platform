# To Run: pytest rest/lecturer/lecturer_test.py

from rest.lecturer.student_management import lecturer_management_route

class TestLecturerManagement:
    """Test the lecturer student management route rendering and behavior."""

    def test_lecturer_management_route_renders(self, app):
        with app.test_request_context("/lecturer/management"):
            response = lecturer_management_route()
            assert "Student Management" in response
            assert "Registered Students" in response