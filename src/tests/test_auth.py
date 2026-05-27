import json
import pytest


# ── helpers ──────────────────────────────────────────────────────────────────

def _register(client, name='Nguyen Van A', email='test@example.com', password='password123'):
    return client.post(
        '/api/register',
        data=json.dumps({'name': name, 'email': email, 'password': password}),
        content_type='application/json',
    )


def _signin(client, email='test@example.com', password='password123'):
    return client.post(
        '/api/signin',
        data=json.dumps({'email': email, 'password': password}),
        content_type='application/json',
    )


def _logout(client):
    return client.post('/api/logout', headers={'X-Requested-With': 'XMLHttpRequest'})


def _clear_session(client):
    with client.session_transaction() as sess:
        sess.clear()


# ── /api/register ─────────────────────────────────────────────────────────────

class TestRegister:
    def test_success_returns_201(self, client):
        resp = _register(client)
        assert resp.status_code == 201

    def test_success_sets_session(self, client):
        _register(client)
        with client.session_transaction() as sess:
            assert 'user_id' in sess

    def test_duplicate_email_returns_409(self, client):
        _register(client)
        _clear_session(client)
        resp = _register(client)
        assert resp.status_code == 409

    def test_empty_name_returns_400(self, client):
        resp = _register(client, name='')
        assert resp.status_code == 400

    def test_whitespace_only_name_returns_400(self, client):
        # validate_input passes '   ' (len=3≥1); AuthService strips it to '' → 400
        resp = _register(client, name='   ')
        assert resp.status_code == 400

    def test_short_password_returns_400(self, client):
        resp = _register(client, password='abc')
        assert resp.status_code == 400

    def test_invalid_email_returns_400(self, client):
        resp = _register(client, email='not-an-email')
        assert resp.status_code == 400

    def test_missing_fields_returns_400(self, client):
        resp = client.post(
            '/api/register',
            data=json.dumps({'email': 'test@example.com'}),
            content_type='application/json',
        )
        assert resp.status_code == 400

    def test_password_not_exposed_in_response(self, client):
        resp = _register(client)
        body = resp.get_json()
        assert 'password' not in str(body)
        assert 'password_hash' not in str(body)


# ── /api/signin ───────────────────────────────────────────────────────────────

class TestSignin:
    def test_success_returns_200(self, client):
        _register(client)
        _clear_session(client)
        resp = _signin(client)
        assert resp.status_code == 200

    def test_success_sets_session(self, client):
        _register(client)
        _clear_session(client)
        _signin(client)
        with client.session_transaction() as sess:
            assert 'user_id' in sess

    def test_wrong_password_returns_401(self, client):
        _register(client)
        _clear_session(client)
        resp = _signin(client, password='wrongpassword')
        assert resp.status_code == 401

    def test_nonexistent_email_returns_401(self, client):
        resp = _signin(client, email='nobody@example.com')
        assert resp.status_code == 401

    def test_email_is_case_insensitive(self, client):
        # DTO lowercases email on both sides, so 'TEST@EXAMPLE.COM' finds the user
        _register(client, email='test@example.com')
        _clear_session(client)
        resp = _signin(client, email='TEST@EXAMPLE.COM')
        assert resp.status_code == 200

    def test_missing_fields_returns_400(self, client):
        resp = client.post(
            '/api/signin',
            data=json.dumps({'email': 'test@example.com'}),
            content_type='application/json',
        )
        assert resp.status_code == 400


# ── /api/logout ───────────────────────────────────────────────────────────────

class TestLogout:
    def test_success_returns_200(self, client):
        _register(client)
        resp = _logout(client)
        assert resp.status_code == 200

    def test_clears_session(self, client):
        _register(client)
        _logout(client)
        with client.session_transaction() as sess:
            assert 'user_id' not in sess

    def test_unauthenticated_returns_401(self, client):
        resp = _logout(client)
        assert resp.status_code == 401

    def test_missing_xhr_header_returns_403(self, client):
        _register(client)
        resp = client.post('/api/logout')
        assert resp.status_code == 403


# ── require_auth decorator ────────────────────────────────────────────────────

class TestRequireAuth:
    def test_api_route_returns_401_when_unauthenticated(self, client):
        # /api/logout uses @require_auth(api=True)
        resp = _logout(client)
        assert resp.status_code == 401

    def test_page_route_redirects_when_unauthenticated(self, client):
        resp = client.get('/home')
        assert resp.status_code == 302
        assert 'signin' in resp.headers.get('Location', '').lower()


# ── auth page routes ──────────────────────────────────────────────────────────

class TestAuthPages:
    def test_signin_page_is_accessible(self, client):
        resp = client.get('/signin')
        assert resp.status_code == 200

    def test_root_redirects_to_signin(self, client):
        resp = client.get('/')
        assert resp.status_code == 200  # / is the signin page itself

    def test_signin_page_redirects_when_logged_in(self, client):
        _register(client)
        resp = client.get('/signin')
        assert resp.status_code == 302

    def test_register_page_redirects_to_signin_tab(self, client):
        resp = client.get('/register')
        assert resp.status_code == 302
        assert 'signin' in resp.headers.get('Location', '').lower()

    def test_register_page_redirects_when_logged_in(self, client):
        _register(client)
        resp = client.get('/register')
        assert resp.status_code == 302
