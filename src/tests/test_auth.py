"""
Auth tests — two levels:
  Route tests  : validate HTTP contract (status codes, session, redirects, headers)
  Service tests: validate business logic (exceptions, hashing, email normalisation)
"""
import json
import pytest


# ── Route-level helpers ───────────────────────────────────────────────────────

def _register(client, name="Nguyen Van A", email="test@example.com", password="password123"):
    return client.post(
        "/api/register",
        data=json.dumps({"name": name, "email": email, "password": password}),
        content_type="application/json",
    )


def _signin(client, email="test@example.com", password="password123"):
    return client.post(
        "/api/signin",
        data=json.dumps({"email": email, "password": password}),
        content_type="application/json",
    )


def _logout(client):
    return client.post("/api/logout", headers={"X-Requested-With": "XMLHttpRequest"})


def _clear_session(client):
    with client.session_transaction() as sess:
        sess.clear()


# =============================================================================
# ROUTE TESTS
# HTTP contract: correct status codes, session handling, redirects, CSRF guard
# =============================================================================

class TestRegisterRoute:
    def test_success_returns_201(self, client):
        assert _register(client).status_code == 201

    def test_success_auto_signs_in(self, client):
        _register(client)
        with client.session_transaction() as sess:
            assert "user_id" in sess

    def test_duplicate_email_returns_409(self, client):
        _register(client)
        _clear_session(client)
        assert _register(client).status_code == 409

    def test_empty_name_returns_400(self, client):
        assert _register(client, name="").status_code == 400

    def test_whitespace_only_name_returns_400(self, client):
        # validate_input lets '   ' through (len≥1); AuthService strips → '' → 400
        assert _register(client, name="   ").status_code == 400

    def test_short_password_returns_400(self, client):
        assert _register(client, password="abc").status_code == 400

    def test_invalid_email_returns_400(self, client):
        assert _register(client, email="not-an-email").status_code == 400

    def test_missing_fields_returns_400(self, client):
        resp = client.post(
            "/api/register",
            data=json.dumps({"email": "test@example.com"}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_password_not_exposed_in_response(self, client):
        body = str(_register(client).get_json())
        assert "password" not in body
        assert "password_hash" not in body


class TestSigninRoute:
    def test_success_returns_200(self, client):
        _register(client)
        _clear_session(client)
        assert _signin(client).status_code == 200

    def test_success_sets_session(self, client):
        _register(client)
        _clear_session(client)
        _signin(client)
        with client.session_transaction() as sess:
            assert "user_id" in sess

    def test_wrong_password_returns_401(self, client):
        _register(client)
        _clear_session(client)
        assert _signin(client, password="wrongpassword").status_code == 401

    def test_nonexistent_email_returns_401(self, client):
        assert _signin(client, email="nobody@example.com").status_code == 401

    def test_email_case_insensitive(self, client):
        _register(client, email="test@example.com")
        _clear_session(client)
        assert _signin(client, email="TEST@EXAMPLE.COM").status_code == 200

    def test_missing_password_returns_400(self, client):
        resp = client.post(
            "/api/signin",
            data=json.dumps({"email": "test@example.com"}),
            content_type="application/json",
        )
        assert resp.status_code == 400


class TestLogoutRoute:
    def test_success_returns_200(self, client):
        _register(client)
        assert _logout(client).status_code == 200

    def test_clears_session(self, client):
        _register(client)
        _logout(client)
        with client.session_transaction() as sess:
            assert "user_id" not in sess

    def test_unauthenticated_returns_401(self, client):
        assert _logout(client).status_code == 401

    def test_missing_xhr_header_returns_403(self, client):
        # Rejects requests without X-Requested-With to mitigate CSRF
        _register(client)
        assert client.post("/api/logout").status_code == 403


class TestRequireAuthDecorator:
    def test_api_prefix_returns_401_json(self, client):
        assert _logout(client).status_code == 401

    def test_page_route_redirects_to_signin(self, client):
        resp = client.get("/home")
        assert resp.status_code == 302
        assert "signin" in resp.headers.get("Location", "").lower()


class TestAuthPages:
    def test_signin_page_accessible(self, client):
        assert client.get("/signin").status_code == 200

    def test_root_serves_signin(self, client):
        assert client.get("/").status_code == 200

    def test_signin_redirects_when_logged_in(self, client):
        _register(client)
        assert client.get("/signin").status_code == 302

    def test_register_page_redirects_to_signin_tab(self, client):
        resp = client.get("/register")
        assert resp.status_code == 302
        assert "signin" in resp.headers.get("Location", "").lower()

    def test_register_page_redirects_when_logged_in(self, client):
        _register(client)
        assert client.get("/register").status_code == 302


# =============================================================================
# SERVICE TESTS
# Business logic: exception semantics, password hashing, email normalisation
# =============================================================================

class TestAuthServiceRegister:
    def test_returns_user_dto_with_id(self, db):
        from src.dto.user_dto import UserRegisterDTO
        from src.services.auth_service import AuthService
        result = AuthService.register(UserRegisterDTO(name="Alice", email="alice@ex.com", password="secret123"))
        assert result.id is not None
        assert result.email == "alice@ex.com"

    def test_password_stored_as_hash(self, db):
        from src.database.models import User
        from src.dto.user_dto import UserRegisterDTO
        from src.services.auth_service import AuthService
        AuthService.register(UserRegisterDTO(name="B", email="b@ex.com", password="secret123"))
        u = User.query.filter_by(email="b@ex.com").first()
        assert u.password_hash != "secret123"

    def test_duplicate_email_raises_email_already_exists(self, db, user):
        from src.dto.user_dto import UserRegisterDTO
        from src.services.auth_service import AuthService, EmailAlreadyExistsError
        with pytest.raises(EmailAlreadyExistsError):
            AuthService.register(UserRegisterDTO(name="X", email="test@example.com", password="secret123"))

    def test_empty_name_raises_auth_error(self, db):
        from src.dto.user_dto import UserRegisterDTO
        from src.services.auth_service import AuthService, AuthError
        with pytest.raises(AuthError):
            AuthService.register(UserRegisterDTO(name="", email="x@ex.com", password="secret123"))

    def test_whitespace_name_raises_auth_error(self, db):
        from src.dto.user_dto import UserRegisterDTO
        from src.services.auth_service import AuthService, AuthError
        with pytest.raises(AuthError):
            AuthService.register(UserRegisterDTO(name="   ", email="y@ex.com", password="secret123"))

    def test_email_stored_lowercase(self, db):
        from src.database.models import User
        from src.dto.user_dto import UserRegisterDTO
        from src.services.auth_service import AuthService
        AuthService.register(UserRegisterDTO(name="C", email="C@UPPER.COM", password="secret123"))
        assert User.query.filter_by(email="c@upper.com").first() is not None


class TestAuthServiceSignin:
    def test_returns_correct_user_dto(self, db, user):
        from src.dto.user_dto import UserLoginDTO
        from src.services.auth_service import AuthService
        result = AuthService.signin(UserLoginDTO(email="test@example.com", password="password123"))
        assert result.id == user.id

    def test_wrong_password_raises_invalid_credentials(self, db, user):
        from src.dto.user_dto import UserLoginDTO
        from src.services.auth_service import AuthService, InvalidCredentialsError
        with pytest.raises(InvalidCredentialsError):
            AuthService.signin(UserLoginDTO(email="test@example.com", password="wrong"))

    def test_nonexistent_email_raises_invalid_credentials(self, db):
        from src.dto.user_dto import UserLoginDTO
        from src.services.auth_service import AuthService, InvalidCredentialsError
        with pytest.raises(InvalidCredentialsError):
            AuthService.signin(UserLoginDTO(email="ghost@ex.com", password="password123"))

    def test_email_lookup_is_case_insensitive(self, db, user):
        from src.dto.user_dto import UserLoginDTO
        from src.services.auth_service import AuthService
        result = AuthService.signin(UserLoginDTO(email="TEST@EXAMPLE.COM", password="password123"))
        assert result.id == user.id
