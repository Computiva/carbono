from tornado.testing import AsyncHTTPTestCase
from tornado.web import create_signed_value

from server import application


class LoginTestCase(AsyncHTTPTestCase):

    def _secure_cookie(self, name, value):
        return create_signed_value(self.get_app().settings["cookie_secret"], name, value)

    def get_app(self):
        return application

    def test_login_form(self):
        response = self.fetch("/login")
        self.assertIn("Username: ", response.body)
        self.assertIn("Password: ", response.body)

    def test_login_action(self):
        headers = {"Cookie": "username=%s" % self._secure_cookie("username", "test user")}
        response = self.fetch("/", headers=headers)
        self.assertIn("test user", response.body)
