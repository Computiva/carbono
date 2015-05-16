from random import getrandbits
from md5 import md5
import re

from tornado.web import Application, authenticated, RequestHandler, StaticFileHandler
from tornado.ioloop import IOLoop
from redis import Redis


class BaseHandler(RequestHandler):

    def get_current_user(self):
        return self.get_secure_cookie("username")


class HomeHandler(BaseHandler):

    @authenticated
    def get(self):
        user_profiles = database.lrange("user:%s:profiles" % self.current_user, 0, -1)
        self.render("home.html", user_profiles=user_profiles)


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


class WorkersHandler(BaseHandler):

    @authenticated
    def get(self):
        user_profiles = database.lrange("user:%s:profiles" % self.current_user, 0, -1)
        if "admin" not in user_profiles:
            self.redirect("/")
            return
        users = list()
        for key in database.keys("*"):
            match = re.search("user:([^:]+):.*", key)
            users.append(match.groups()[0])
        self.render("workers.html", users=users)


class RegisterWorkerHandler(BaseHandler):

    @authenticated
    def get(self):
        user_profiles = database.lrange("user:%s:profiles" % self.current_user, 0, -1)
        if "admin" not in user_profiles:
            self.redirect("/")
            return
        self.render("register_worker.html")

    @authenticated
    def post(self):
        user_profiles = database.lrange("user:%s:profiles" % self.current_user, 0, -1)
        if "admin" not in user_profiles:
            self.redirect("/")
            return
        username = self.get_argument("username")
        complete_name = self.get_argument("complete_name")
        profiles = self.get_argument("profiles")
        database.set("user:%s:password" % username, md5(username).hexdigest())
        database.set("user:%s:complete_name" % username, complete_name)
        for profile in profiles:
            database.rpush("user:%s:profiles" % username, profile)
        self.redirect("/workers")


class RemoveWorkerHandler(BaseHandler):

    @authenticated
    def get(self):
        user_profiles = database.lrange("user:%s:profiles" % self.current_user, 0, -1)
        if "admin" not in user_profiles:
            self.redirect("/")
            return
        username = self.get_argument("username")
        database.delete("user:%s:profiles" % username)
        self.redirect("/workers")


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
    (r"/workers", WorkersHandler),
    (r"/register_worker", RegisterWorkerHandler),
    (r"/remove_worker", RemoveWorkerHandler),
    (r"/(.*\.css)", StaticFileHandler, {"path": "./www/styles"}),
    (r"/(.*\.js)", StaticFileHandler, {"path": "./www/scripts"}),
], **settings)
database = Redis()

if __name__ == "__main__":
    application.listen(8000)
    IOLoop.instance().start()
