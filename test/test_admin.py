from urllib import urlencode
from md5 import md5

from tornado.testing import AsyncHTTPTestCase
from tornado.web import create_signed_value
from redis import Redis

from server import application
import server


class AdminTestCase(AsyncHTTPTestCase):

    def _secure_cookie(self, name, value):
        return create_signed_value(self.get_app().settings["cookie_secret"], name, value)

    def get_app(self):
        return application

    def setUp(self):
        server.database = Redis(db=1)
        server.database.flushdb()
        server.database.rpush("user:test_admin:profiles", "admin")
        server.database.rpush("user:test_seller:profiles", "seller")
        server.database.rpush("user:test_register:profiles", "register")
        super(AdminTestCase, self).setUp()

    def tearDown(self):
        server.database.flushdb()
        super(AdminTestCase, self).tearDown()

    def test_authorize_admin_to_view_workers_page(self):
        headers = {"Cookie": "username=%s" % self._secure_cookie("username", "test_admin")}
        response = self.fetch("/", headers=headers)
        self.assertIn("/workers", response.body)
        response = self.fetch("/workers", headers=headers)
        self.assertIn("/register_worker", response.body)

    def test_do_not_authorize_other_users_to_view_workers_page(self):
        headers = {"Cookie": "username=%s" % self._secure_cookie("username", "test_seller")}
        response = self.fetch("/", headers=headers)
        self.assertNotIn("/workers", response.body)
        self.assertEquals(self.fetch("/workers", headers=headers).body, self.fetch("/", headers=headers).body)
        headers = {"Cookie": "username=%s" % self._secure_cookie("username", "test_register")}
        response = self.fetch("/", headers=headers)
        self.assertNotIn("/workers", response.body)
        self.assertEquals(self.fetch("/workers", headers=headers).body, self.fetch("/", headers=headers).body)

    def test_authorize_admin_to_register_worker(self):
        headers = {"Cookie": "username=%s" % self._secure_cookie("username", "test_admin")}
        response = self.fetch("/register_worker", headers=headers)
        self.assertIn("Username: ", response.body)
        self.assertIn("Complete name: ", response.body)
        self.assertIn("Profiles:", response.body)
        self.assertIn("admin", response.body)
        self.assertIn("seller", response.body)
        self.assertIn("register", response.body)

    def test_do_not_authorize_other_users_to_register_worker(self):
        headers = {"Cookie": "username=%s" % self._secure_cookie("username", "test_seller")}
        self.assertEquals(self.fetch("/register_worker", headers=headers).body, self.fetch("/", headers=headers).body)
        headers = {"Cookie": "username=%s" % self._secure_cookie("username", "test_register")}
        self.assertEquals(self.fetch("/register_worker", headers=headers).body, self.fetch("/", headers=headers).body)
        headers = {"Cookie": "username=%s" % self._secure_cookie("username", "test_seller")}
        body = urlencode({
            "username": "test_new_worker",
            "complete_name": "New Worker",
            "profiles": ["seller", "register"],
        })
        self.fetch("/register_worker", headers=headers, method="POST", body=body)
        self.assertNotIn("user:test_new_worker:profiles", server.database.keys())

    def test_do_not_authorize_other_users_to_remove_worker(self):
        headers = {"Cookie": "username=%s" % self._secure_cookie("username", "test_register")}
        self.fetch("/remove_worker?username=test_seller", headers=headers)
        self.assertIn("user:test_seller:profiles", server.database.keys())

    def test_list_workers(self):
        headers = {"Cookie": "username=%s" % self._secure_cookie("username", "test_admin")}
        response = self.fetch("/workers", headers=headers)
        self.assertIn("test_admin", response.body)
        self.assertIn("test_seller", response.body)
        self.assertIn("test_register", response.body)

    def test_remove_worker(self):
        headers = {"Cookie": "username=%s" % self._secure_cookie("username", "test_admin")}
        self.fetch("/remove_worker?username=test_seller", headers=headers)
        response = self.fetch("/workers", headers=headers)
        self.assertNotIn("test_seller", response.body)

    def test_register_worker(self):
        headers = {"Cookie": "username=%s" % self._secure_cookie("username", "test_admin")}
        body = urlencode({
            "username": "test_new_worker",
            "complete_name": "New Worker",
            "profiles": ["seller", "register"],
        })
        self.fetch("/register_worker", headers=headers, method="POST", body=body)
        response = self.fetch("/workers", headers=headers)
        self.assertIn("test_new_worker", response.body)
