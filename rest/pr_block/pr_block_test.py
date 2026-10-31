# To Run: pytest rest/pr_block_test.py

from rest.pr_block.pr_block import pr_block_route


class TestPrBlockRoute:
    """Test the pr_block_route function"""

    def test_pr_block_route_renders(self, app):
        # ARRANGE / ACT
        with app.test_request_context("/"):
            response = pr_block_route()

        # ASSERT
        assert "PR Block" in response
