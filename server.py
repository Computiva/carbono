from random import getrandbits
from md5 import md5

from tornado.web import Application, authenticated, RequestHandler
from tornado.ioloop import IOLoop
from redis import Redis


class BaseHandler(RequestHandler):

    def get_current_user(self):
        return self.get_secure_cookie("username")


class HomeHandler(BaseHandler):

    @authenticated
    def get(self):
        self.render("home.html")


class LoginHandler(BaseHandler):

    def get(self):
        self.render("login.html")

    def post(self):
        username = self.get_argument("username")
        password = self.get_argument("password")
        if database.get("user:%s:password" % username) == md5(password).hexdigest():
            self.set_secure_cookie("username", username)
            self.redirect("/")
            return
        self.write("Wrong login or password! <a href=\"/login\">back</a>")


class LogoutHandler(BaseHandler):

    def get(self):
        self.clear_cookie("username")
        self.redirect("/login")


settings = {
    "cookie_secret": "%X" % getrandbits(1024),
    "login_url": "/login",
    "template_path": "./www",
    "debug": True,
}
application = Application([
    (r"/", HomeHandler),
    (r"/login", LoginHandler),
    (r"/logout", LogoutHandler),
], **settings)
database = Redis()

if __name__ == "__main__":
    application.listen(8000)
    IOLoop.instance().start()
