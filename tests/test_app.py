"""
tests/test_app.py — Comprehensive test suite for CottonGreen AI
Covers: backend, security, API, auth, performance, failure cases
"""
import io
import os
import sys
import time
import json
import unittest
from PIL import Image

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from config import TestingConfig
from db_models import db, User, ScanHistory, APIKey


def make_test_image(size=(224, 224), color=(0, 128, 0)):
    """Create a valid test image in memory."""
    img = Image.new("RGB", size, color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf


class BaseTestCase(unittest.TestCase):
    """Base with app setup, teardown, and helpers."""

    def setUp(self):
        self.app = create_app(TestingConfig())
        self.app.config["WTF_CSRF_ENABLED"] = False
        self.app.config["LOGIN_DISABLED"]   = False
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def register_user(self, username="testuser", email="test@test.com",
                      password="TestPass123", confirm="TestPass123"):
        return self.client.post("/auth/register", data={
            "username": username, "email": email,
            "password": password, "confirm_password": confirm,
        }, follow_redirects=True)

    def login_user(self, identifier="testuser", password="TestPass123"):
        return self.client.post("/auth/login", data={
            "identifier": identifier, "password": password,
        }, follow_redirects=True)

    def create_logged_in_user(self):
        self.register_user()
        return User.query.filter_by(username="testuser").first()


# ═══════════════════════════════════════════════════════════════
#  1. BACKEND TESTS
# ═══════════════════════════════════════════════════════════════

class TestHealthEndpoint(BaseTestCase):
    def test_health_endpoint_returns_json(self):
        r = self.client.get("/health")
        data = r.get_json()
        self.assertIn("status", data)
        self.assertIn("version", data)
        self.assertIn(r.status_code, [200, 503])


class TestDatabaseModels(BaseTestCase):
    def test_create_user(self):
        u = User(username="john", email="john@x.com")
        u.set_password("Secure123")
        db.session.add(u)
        db.session.commit()
        self.assertIsNotNone(u.id)
        self.assertTrue(u.check_password("Secure123"))
        self.assertFalse(u.check_password("wrong"))

    def test_first_user_is_admin(self):
        self.register_user()
        u = User.query.first()
        self.assertTrue(u.is_admin)

    def test_scan_history_creation(self):
        self.create_logged_in_user()
        u = User.query.first()
        scan = ScanHistory(
            user_id=u.id, disease="Curl Virus",
            severity="Very High", confidence=95.5,
        )
        db.session.add(scan)
        db.session.commit()
        self.assertEqual(u.scans.count(), 1)
        d = scan.to_dict()
        self.assertEqual(d["disease"], "Curl Virus")

    def test_api_key_generation(self):
        self.create_logged_in_user()
        u = User.query.first()
        key = APIKey(user_id=u.id, key=APIKey.generate_key(), name="TestKey")
        db.session.add(key)
        db.session.commit()
        self.assertTrue(key.key.startswith("cgai_"))
        self.assertEqual(len(key.key), 53)  # "cgai_" + 48 hex chars


class TestConfigResolution(BaseTestCase):
    def test_testing_config_applied(self):
        self.assertTrue(self.app.config["TESTING"])
        self.assertFalse(self.app.config["WTF_CSRF_ENABLED"])


# ═══════════════════════════════════════════════════════════════
#  2. AUTH / SECURITY TESTS
# ═══════════════════════════════════════════════════════════════

class TestAuthRegistration(BaseTestCase):
    def test_register_success(self):
        r = self.register_user()
        self.assertEqual(r.status_code, 200)
        self.assertIsNotNone(User.query.filter_by(username="testuser").first())

    def test_register_duplicate_username(self):
        self.register_user()
        self.client.get("/auth/logout")
        r = self.register_user(email="other@test.com")
        self.assertIn(b"already taken", r.data)

    def test_register_duplicate_email(self):
        self.register_user()
        self.client.get("/auth/logout")
        r = self.register_user(username="testuser2")
        self.assertIn(b"already exists", r.data)

    def test_register_invalid_username(self):
        r = self.register_user(username="ab")  # too short
        self.assertIn(b"3", r.data)

    def test_register_weak_password(self):
        r = self.register_user(password="123", confirm="123")
        self.assertIn(b"at least", r.data)

    def test_register_password_mismatch(self):
        r = self.register_user(password="TestPass123", confirm="WrongPass")
        self.assertIn(b"do not match", r.data)


class TestAuthLogin(BaseTestCase):
    def test_login_success(self):
        self.register_user()
        self.client.get("/auth/logout")
        r = self.login_user()
        self.assertEqual(r.status_code, 200)

    def test_login_wrong_password(self):
        self.register_user()
        self.client.get("/auth/logout")
        r = self.login_user(password="WrongPass")
        self.assertIn(b"Invalid", r.data)

    def test_login_nonexistent_user(self):
        r = self.login_user(identifier="nobody")
        self.assertIn(b"Invalid", r.data)

    def test_logout(self):
        self.create_logged_in_user()
        r = self.client.get("/auth/logout", follow_redirects=True)
        self.assertEqual(r.status_code, 200)

    def test_protected_route_redirect(self):
        r = self.client.get("/", follow_redirects=False)
        self.assertIn(r.status_code, [302, 401])


class TestBruteForceProtection(BaseTestCase):
    def test_account_lockout(self):
        self.register_user()
        self.client.get("/auth/logout")
        for _ in range(6):
            self.login_user(password="wrong")
        u = User.query.first()
        self.assertTrue(u.is_locked())


class TestSecurityHeaders(BaseTestCase):
    def test_security_headers_present(self):
        self.create_logged_in_user()
        r = self.client.get("/")
        self.assertIn("Content-Security-Policy", r.headers)
        self.assertIn("X-Content-Type-Options", r.headers)
        self.assertEqual(r.headers["X-Content-Type-Options"], "nosniff")
        self.assertIn("X-Frame-Options", r.headers)
        self.assertIn("X-XSS-Protection", r.headers)

    def test_response_time_header(self):
        self.create_logged_in_user()
        r = self.client.get("/")
        self.assertIn("X-Response-Time", r.headers)


# ═══════════════════════════════════════════════════════════════
#  3. API TESTS
# ═══════════════════════════════════════════════════════════════

class TestAPIAuth(BaseTestCase):
    def test_predict_requires_auth(self):
        r = self.client.post("/api/v1/predict")
        self.assertEqual(r.status_code, 401)

    def test_history_requires_auth(self):
        r = self.client.get("/api/v1/history")
        self.assertEqual(r.status_code, 401)

    def test_api_key_auth(self):
        self.create_logged_in_user()
        u = User.query.first()
        key = APIKey(user_id=u.id, key=APIKey.generate_key(), name="Test")
        db.session.add(key)
        db.session.commit()
        self.client.get("/auth/logout")
        r = self.client.get("/api/v1/history",
                            headers={"X-API-Key": key.key})
        self.assertEqual(r.status_code, 200)


class TestAPIPredict(BaseTestCase):
    def test_predict_no_file(self):
        self.create_logged_in_user()
        r = self.client.post("/api/v1/predict")
        self.assertEqual(r.status_code, 400)
        self.assertIn("No file", r.get_json()["error"])

    def test_predict_invalid_image(self):
        self.create_logged_in_user()
        data = {"file": (io.BytesIO(b"not an image"), "bad.jpg")}
        r = self.client.post("/api/v1/predict", data=data,
                             content_type="multipart/form-data")
        self.assertEqual(r.status_code, 400)


class TestAPIHistory(BaseTestCase):
    def test_history_empty(self):
        self.create_logged_in_user()
        r = self.client.get("/api/v1/history")
        data = r.get_json()
        self.assertEqual(data["total"], 0)
        self.assertEqual(data["scans"], [])

    def test_history_pagination(self):
        self.create_logged_in_user()
        u = User.query.first()
        for i in range(5):
            db.session.add(ScanHistory(
                user_id=u.id, disease="Healthy Leaf",
                severity="None", confidence=90+i,
            ))
        db.session.commit()
        r = self.client.get("/api/v1/history?per_page=2&page=1")
        data = r.get_json()
        self.assertEqual(len(data["scans"]), 2)
        self.assertEqual(data["total"], 5)


class TestAPIKeyManagement(BaseTestCase):
    def test_create_api_key(self):
        self.create_logged_in_user()
        r = self.client.post("/api/v1/keys",
                             data=json.dumps({"name": "MyKey"}),
                             content_type="application/json")
        self.assertEqual(r.status_code, 201)
        data = r.get_json()
        self.assertIn("key", data)
        self.assertTrue(data["key"].startswith("cgai_"))

    def test_revoke_api_key(self):
        self.create_logged_in_user()
        u = User.query.first()
        key = APIKey(user_id=u.id, key=APIKey.generate_key(), name="Del")
        db.session.add(key)
        db.session.commit()
        r = self.client.delete(f"/api/v1/keys/{key.id}")
        self.assertEqual(r.status_code, 200)
        self.assertFalse(APIKey.query.get(key.id).is_active)

    def test_max_api_keys_limit(self):
        self.create_logged_in_user()
        u = User.query.first()
        for i in range(5):
            db.session.add(APIKey(user_id=u.id, key=APIKey.generate_key(), name=f"K{i}"))
        db.session.commit()
        r = self.client.post("/api/v1/keys",
                             data=json.dumps({"name": "Extra"}),
                             content_type="application/json")
        self.assertEqual(r.status_code, 400)


class TestAPIStats(BaseTestCase):
    def test_stats_endpoint(self):
        self.create_logged_in_user()
        r = self.client.get("/api/v1/stats")
        data = r.get_json()
        self.assertIn("total_scans", data)
        self.assertIn("health_rate", data)


# ═══════════════════════════════════════════════════════════════
#  4. ADMIN TESTS
# ═══════════════════════════════════════════════════════════════

class TestAdminAccess(BaseTestCase):
    def test_admin_dashboard_accessible(self):
        self.create_logged_in_user()  # first user = admin
        r = self.client.get("/admin/")
        self.assertEqual(r.status_code, 200)

    def test_non_admin_blocked(self):
        self.create_logged_in_user()
        self.client.get("/auth/logout")
        self.register_user(username="regular", email="reg@x.com")
        r = self.client.get("/admin/")
        self.assertEqual(r.status_code, 403)

    def test_toggle_user(self):
        self.create_logged_in_user()
        u2 = User(username="target", email="t@x.com")
        u2.set_password("TestPass123")
        db.session.add(u2)
        db.session.commit()
        r = self.client.post(f"/admin/api/users/{u2.id}/toggle")
        self.assertEqual(r.status_code, 200)
        self.assertFalse(User.query.get(u2.id).is_active)

    def test_cannot_toggle_self(self):
        self.create_logged_in_user()
        u = User.query.first()
        r = self.client.post(f"/admin/api/users/{u.id}/toggle")
        self.assertEqual(r.status_code, 400)

    def test_promote_user(self):
        self.create_logged_in_user()
        u2 = User(username="promo", email="p@x.com")
        u2.set_password("TestPass123")
        db.session.add(u2)
        db.session.commit()
        r = self.client.post(f"/admin/api/users/{u2.id}/promote")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(User.query.get(u2.id).is_admin)


# ═══════════════════════════════════════════════════════════════
#  5. PERFORMANCE TESTS
# ═══════════════════════════════════════════════════════════════

class TestPerformance(BaseTestCase):
    def test_health_response_time(self):
        """Health endpoint should respond in < 200ms."""
        t0 = time.time()
        self.client.get("/health")
        elapsed = (time.time() - t0) * 1000
        self.assertLess(elapsed, 200, f"Health took {elapsed:.0f}ms")

    def test_auth_page_response_time(self):
        """Login page should render in < 500ms."""
        t0 = time.time()
        self.client.get("/auth/login")
        elapsed = (time.time() - t0) * 1000
        self.assertLess(elapsed, 500, f"Login page took {elapsed:.0f}ms")

    def test_concurrent_registrations(self):
        """Multiple sequential registrations should succeed."""
        for i in range(10):
            r = self.register_user(
                username=f"user{i}", email=f"u{i}@x.com",
                password="TestPass123", confirm="TestPass123",
            )
            self.client.get("/auth/logout")
        self.assertEqual(User.query.count(), 10)


# ═══════════════════════════════════════════════════════════════
#  6. FAILURE / EDGE CASE TESTS
# ═══════════════════════════════════════════════════════════════

class TestFailureCases(BaseTestCase):
    def test_404_page(self):
        r = self.client.get("/nonexistent-page")
        self.assertEqual(r.status_code, 404)

    def test_oversized_upload(self):
        self.create_logged_in_user()
        # 20 MB file (exceeds 16 MB limit)
        big = io.BytesIO(b"x" * (20 * 1024 * 1024))
        r = self.client.post("/api/v1/predict",
                             data={"file": (big, "huge.jpg")},
                             content_type="multipart/form-data")
        self.assertIn(r.status_code, [400, 413])

    def test_wrong_file_type(self):
        self.create_logged_in_user()
        data = {"file": (io.BytesIO(b"fake pdf data"), "test.pdf")}
        r = self.client.post("/api/v1/predict", data=data,
                             content_type="multipart/form-data")
        self.assertEqual(r.status_code, 400)

    def test_empty_form_submission(self):
        r = self.client.post("/auth/login", data={}, follow_redirects=True)
        self.assertEqual(r.status_code, 200)

    def test_xss_in_username(self):
        r = self.register_user(username="<script>alert(1)</script>")
        self.assertNotIn(b"<script>alert(1)</script>", r.data)

    def test_sql_injection_login(self):
        r = self.login_user(identifier="' OR 1=1 --", password="x")
        self.assertIn(b"Invalid", r.data)

    def test_deactivated_user_cannot_login(self):
        self.create_logged_in_user()
        u = User.query.first()
        self.client.get("/auth/logout")
        # Deactivate
        u.is_active = False
        db.session.commit()
        r = self.login_user()
        self.assertIn(b"deactivated", r.data.lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
