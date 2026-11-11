# To Run: pytest rest/login/logout_test.py

from rest.login.logout import SIGN_OUT_MESSAGE


class TestLogoutRoute:
    """Test the logout_route function"""

    def test_logout_redirects_to_login(self, client):
        # ACT
        response = client.post("/logout")

        # ASSERT
        assert response.status_code == 302
        assert response.headers["Location"] == "/login"
        assert response.headers["Cache-Control"] == "no-store"

    def test_logout_clears_session(self, client):
        # ARRANGE
        with client.session_transaction() as sess:
            sess["user_id"] = 42

        # ACT
        client.post("/logout")

        # ASSERT
        with client.session_transaction() as sess:
            assert "user_id" not in sess

    def test_logout_shows_confirmation_on_login_page(self, client):
        # ACT
        response = client.post("/logout", follow_redirects=True)

        # ASSERT
        assert response.status_code == 200
        assert SIGN_OUT_MESSAGE.encode() in response.data

    def test_confirmation_only_shown_once(self, client):
        # ARRANGE
        client.post("/logout", follow_redirects=True)

        # ACT
        response = client.get("/login")

        # ASSERT
        assert SIGN_OUT_MESSAGE.encode() not in response.data

    def test_logout_rejects_get(self, client):
        # ACT
        response = client.get("/logout")

        # ASSERT
        assert response.status_code == 405
