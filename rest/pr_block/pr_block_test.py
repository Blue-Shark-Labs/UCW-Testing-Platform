# To Run: pytest rest/pr_block_test.py

from rest.pr_block.pr_block import pr_block_route


class TestPrBlockRoute:
    """Test the pr_block_route function"""

    def test_pr_block_route_redirects_when_not_logged_in(self, app):
        # ARRANGE / ACT
        with app.test_request_context("/pr-block/"):
            response = pr_block_route()

        # ASSERT
        assert response.status_code == 302
        assert "/login" in response.location

    def test_pr_block_route_renders(self, app):
        # ARRANGE / ACT
        with app.test_request_context("/pr-block/"):
            from flask import session

            session["user_id"] = "11111111-1111-1111-1111-111111111111"
            session["role"] = "student"
            response = pr_block_route()

        # ASSERT
        assert b"PR Block" in response.data
