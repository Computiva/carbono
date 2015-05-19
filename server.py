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
        if database.get("user:%s:password" % username) != md5(password).hexdigest():
            self.render("login.html", error_message="Wrong login or password!")
            return
        self.set_secure_cookie("username", username)
        if username == password:
            self.redirect("/manage_account")
            return
        self.redirect("/")
        return


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
        for key in database.keys("user:*"):
            username = re.search("user:([^:]+):.*", key).groups()[0]
            if username not in users:
                users.append(username)
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
        database.set("user:%s:password" % username, md5(username).hexdigest())
        database.set("user:%s:complete_name" % username, complete_name)
        for profile in self.request.arguments["profiles"]:
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
        for key in database.keys("user:%s:*" % username):
            database.delete(key)
        self.redirect("/workers")


class ManageAccountHandler(BaseHandler):

    @authenticated
    def get(self):
        complete_name = database.get("user:%s:complete_name" % self.current_user)
        user_profiles = database.lrange("user:%s:profiles" % self.current_user, 0, -1)
        self.render("manage_account.html", complete_name=complete_name, user_profiles=user_profiles)

    @authenticated
    def post(self):
        username = self.current_user
        password = self.get_argument("password")
        confirm_password = self.get_argument("confirm_password")
        complete_name = self.get_argument("complete_name")
        if password != confirm_password:
            user_profiles = database.lrange("user:%s:profiles" % self.current_user, 0, -1)
            self.render("manage_account.html", complete_name=complete_name, user_profiles=user_profiles, error_message="Passwords don't match.")
            return
        if password:
            database.set("user:%s:password" % username, md5(password).hexdigest())
        database.set("user:%s:complete_name" % username, complete_name)
        if "profiles" in self.request.arguments.keys():
            database.delete("user:%s:profiles" % username)
            for profile in self.request.arguments["profiles"]:
                database.rpush("user:%s:profiles" % username, profile)
        self.redirect("/workers")


class ClientsHandler(BaseHandler):

    @authenticated
    def get(self):
        user_profiles = database.lrange("user:%s:profiles" % self.current_user, 0, -1)
        if "seller" not in user_profiles and "register" not in user_profiles:
            self.redirect("/")
            return
        clients = list()
        for key in database.keys("client:*"):
            client_id = re.search("client:([^:]+):.*", key).groups()[0]
            if client_id not in map(lambda client: client["id"], clients):
                clients.append({
                    "id": client_id,
                    "complete_name": database.get("client:%s:complete_name" % client_id)
                })
        user_profiles = database.lrange("user:%s:profiles" % self.current_user, 0, -1)
        self.render("clients.html", clients=clients, user_profiles=user_profiles)


class RegisterClientHandler(BaseHandler):

    @authenticated
    def get(self):
        user_profiles = database.lrange("user:%s:profiles" % self.current_user, 0, -1)
        if "register" not in user_profiles:
            self.redirect("/")
            return
        self.render("register_client.html")

    @authenticated
    def post(self):
        user_profiles = database.lrange("user:%s:profiles" % self.current_user, 0, -1)
        if "register" not in user_profiles:
            self.redirect("/")
            return
        complete_name = self.get_argument("complete_name")
        address = self.get_argument("address")
        client_ids = ["0"]
        for key in database.keys("client:*"):
            client_id = re.search("client:([^:]+):.*", key).groups()[0]
            if client_id not in client_ids:
                client_ids.append(client_id)
        client_id = str(max(map(int, client_ids)) + 1)
        database.set("client:%s:complete_name" % client_id, complete_name)
        database.set("client:%s:address" % client_id, address)
        self.redirect("/clients")


class ViewClientHandler(BaseHandler):

    @authenticated
    def get(self):
        user_profiles = database.lrange("user:%s:profiles" % self.current_user, 0, -1)
        if "seller" not in user_profiles:
            self.redirect("/")
            return
        client_id = self.get_argument("client_id")
        client = {
            "complete_name": database.get("client:%s:complete_name" % client_id),
            "address": database.get("client:%s:address" % client_id),
        }
        self.render("client.html", client=client)


class RemoveClientHandler(BaseHandler):

    @authenticated
    def get(self):
        user_profiles = database.lrange("user:%s:profiles" % self.current_user, 0, -1)
        if "register" not in user_profiles:
            self.redirect("/")
            return
        client_id = self.get_argument("client_id")
        for key in database.keys("client:%s:*" % client_id):
            database.delete(key)
        self.redirect("/clients")


class ProductsHandler(BaseHandler):

    @authenticated
    def get(self):
        user_profiles = database.lrange("user:%s:profiles" % self.current_user, 0, -1)
        if "register" not in user_profiles:
            self.redirect("/")
            return
        products = list()
        for key in database.keys("product:*"):
            product_id = re.search("product:([^:]+):.*", key).groups()[0]
            if product_id not in map(lambda product: product["id"], products):
                products.append({
                    "id": product_id,
                    "name": database.get("product:%s:name" % product_id),
                    "amount": database.get("product:%s:amount" % product_id),
                })
        self.render("products.html", products=products)


class RegisterProductHandler(BaseHandler):

    @authenticated
    def get(self):
        user_profiles = database.lrange("user:%s:profiles" % self.current_user, 0, -1)
        if "register" not in user_profiles:
            self.redirect("/")
            return
        self.render("register_product.html")

    @authenticated
    def post(self):
        user_profiles = database.lrange("user:%s:profiles" % self.current_user, 0, -1)
        if "register" not in user_profiles:
            self.redirect("/")
            return
        name = self.get_argument("name")
        amount = self.get_argument("amount")
        product_ids = ["0"]
        for key in database.keys("product:*"):
            product_id = re.search("product:([^:]+):.*", key).groups()[0]
            if product_id not in product_ids:
                product_ids.append(product_id)
        product_id = str(max(map(int, product_ids)) + 1)
        database.set("product:%s:name" % product_id, name)
        database.set("product:%s:amount" % product_id, amount)
        self.redirect("/products")


class ViewProductHandler(BaseHandler):

    @authenticated
    def get(self):
        user_profiles = database.lrange("user:%s:profiles" % self.current_user, 0, -1)
        if "register" not in user_profiles:
            self.redirect("/")
            return
        product_id = self.get_argument("product_id")
        product = {
            "name": database.get("product:%s:name" % product_id),
            "amount": database.get("product:%s:amount" % product_id),
        }
        self.render("product.html", product=product)


class RemoveProductHandler(BaseHandler):

    @authenticated
    def get(self):
        user_profiles = database.lrange("user:%s:profiles" % self.current_user, 0, -1)
        if "register" not in user_profiles:
            self.redirect("/")
            return
        product_id = self.get_argument("product_id")
        for key in database.keys("product:%s:*" % product_id):
            database.delete(key)
        self.redirect("/products")


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
    (r"/manage_account", ManageAccountHandler),
    (r"/clients", ClientsHandler),
    (r"/register_client", RegisterClientHandler),
    (r"/client", ViewClientHandler),
    (r"/remove_client", RemoveClientHandler),
    (r"/products", ProductsHandler),
    (r"/register_product", RegisterProductHandler),
    (r"/product", ViewProductHandler),
    (r"/remove_product", RemoveProductHandler),
    (r"/(.*\.css)", StaticFileHandler, {"path": "./www/styles"}),
    (r"/(.*\.js)", StaticFileHandler, {"path": "./www/scripts"}),
], **settings)
database = Redis()

if __name__ == "__main__":
    application.listen(8000)
    IOLoop.instance().start()
