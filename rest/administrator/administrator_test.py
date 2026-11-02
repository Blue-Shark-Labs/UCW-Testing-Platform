# To Run: pytest rest/administrator_test.py

from rest.administrator.administrator import administrator_view_subjects_route


class TestRoute:
    """Test the administrator_view_subjects_route function"""

    def test_administrator_view_subjects_route_renders(self, app):
        # ARRANGE / ACT
        with app.test_request_context("/"):
            response = administrator_view_subjects_route()

        # ASSERT
        assert "Administrator" in response
