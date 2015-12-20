# -*- coding: UTF-8 -*-

from random import getrandbits
from md5 import md5
import json
import time
import re
import os

os.system("clear")
os.system("echo The server is now connected...")
#os.system("date >> logs.txt")
os.system("date")

from tornado.web import Application, authenticated, RequestHandler, StaticFileHandler
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado import locale
from redis import Redis



LOCALE_DESCRIPTIONS = {
    "en_US": "English (United States)",
    "pt_BR": "Português (Brasil)",
}


class BaseHandler(RequestHandler):

    def get_current_user(self):
        return self.get_secure_cookie("username")

    def get_user_locale(self):
        return locale.get(database.get("user:%s:locale_code" % self.current_user))


class HomeHandler(BaseHandler):

    @authenticated
    def get(self):
        user_profiles = database.lrange("user:%s:profiles" % self.current_user, 0, -1)
        self.render("home.html", user_profiles=user_profiles)


class LoginHandler(BaseHandler):

    def get(self):
        self.render("login.html", databases=databases.keys())

    def post(self):
        database_name = self.get_argument("database_name", databases.keys()[0])
        username = self.get_argument("username")
        password = self.get_argument("password")
        global database
        database = Redis(db=int(databases.get(database_name, 0)))
        if database.get("user:%s:password" % username) != md5(password).hexdigest():
            self.render("login.html", error_message="Wrong login or password!", databases=databases.keys())
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
    def get(self, **kwargs):
        user_profiles = database.lrange("user:%s:profiles" % self.current_user, 0, -1)
        if "admin" not in user_profiles:
            self.redirect("/")
            return
        locale_codes = list()
        for locale_code in locale.get_supported_locales():
            locale_codes.append({
                "code": locale_code,
                "description": LOCALE_DESCRIPTIONS[locale_code],
            })
        self.render("register_worker.html", locale_codes=locale_codes, **kwargs)

    @authenticated
    def post(self):
        user_profiles = database.lrange("user:%s:profiles" % self.current_user, 0, -1)
        if "admin" not in user_profiles:
            self.redirect("/")
            return
        username = self.get_argument("username")
        if not re.search(r"^[a-zA-Z0-9_]+$", username):
            self.get(error_message="Username should contain just letters, numbers or underlines.")
            return
        complete_name = self.get_argument("complete_name")
        locale_code = self.get_argument("locale_code")
        database.set("user:%s:password" % username, md5(username).hexdigest())
        database.set("user:%s:complete_name" % username, complete_name)
        database.set("user:%s:locale_code" % username, locale_code)
        for profile in self.request.arguments.get("profiles", list()):
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
    def get(self, **kwargs):
        user_profiles = database.lrange("user:%s:profiles" % self.current_user, 0, -1)
        if "register" not in user_profiles:
            self.redirect("/")
            return
        self.render("register_product.html", **kwargs)

    @authenticated
    def post(self):
        user_profiles = database.lrange("user:%s:profiles" % self.current_user, 0, -1)
        if "register" not in user_profiles:
            self.redirect("/")
            return
        name = self.get_argument("name")
        amount = self.get_argument("amount")
        if not re.search(r"^[0-9]+$", amount):
            self.get(error_message="Amount should be integer number.")
            return
        price = self.get_argument("price")
        if not re.search(r"^[0-9]+[.0-9]*$", price):
            self.get(error_message="Price should be float number.")
            return
        product_ids = ["0"]
        for key in database.keys("product:*"):
            product_id = re.search("product:([^:]+):.*", key).groups()[0]
            if product_id not in product_ids:
                product_ids.append(product_id)
        product_id = str(max(map(int, product_ids)) + 1)
        database.set("product:%s:name" % product_id, name)
        database.set("product:%s:amount" % product_id, amount)
        database.set("product:%s:price" % product_id, price)
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
            "price": database.get("product:%s:price" % product_id),
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


class SalesHandler(BaseHandler):

    @authenticated
    def get(self):
        user_profiles = database.lrange("user:%s:profiles" % self.current_user, 0, -1)
        if "seller" not in user_profiles:
            self.redirect("/")
            return
        sales = list()
        for key in database.keys("sale:*"):
            sale_id = re.search("sale:([^:]+):.*", key).groups()[0]
            if sale_id not in map(lambda sale: sale["id"], sales):
                sales.append({
                    "id": sale_id,
                    "client": database.get("sale:%s:client" % sale_id),
                })
        self.render("sales.html", sales=sales)


class RegisterSaleHandler(BaseHandler):

    @authenticated
    def get(self):
        user_profiles = database.lrange("user:%s:profiles" % self.current_user, 0, -1)
        if "seller" not in user_profiles:
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
        products = list()
        for key in database.keys("product:*"):
            product_id = re.search("product:([^:]+):.*", key).groups()[0]
            if product_id not in map(lambda product: product["id"], products):
                products.append({
                    "id": product_id,
                    "name": database.get("product:%s:name" % product_id),
                    "amount": database.get("product:%s:amount" % product_id),
                    "price": database.get("product:%s:price" % product_id),
                })
        today = time.strftime(r"%d/%m/%Y")
        self.render("register_sale.html", clients=clients, products=products, today=today)

    @authenticated
    def post(self):
        user_profiles = database.lrange("user:%s:profiles" % self.current_user, 0, -1)
        if "seller" not in user_profiles:
            self.redirect("/")
            return
        client = self.get_argument("client")
        sale_term = self.get_argument("sale_terms")
        initial_date = self.get_argument("initial_date")
        times = self.get_argument("times")
        products = json.loads(self.get_argument("products_list"))
        sale_ids = ["0"]
        for key in database.keys("sale:*"):
            sale_id = re.search("sale:([^:]+):.*", key).groups()[0]
            if sale_id not in sale_ids:
                sale_ids.append(sale_id)
        sale_id = str(max(map(int, sale_ids)) + 1)
        for product in products:
            database.set("sale:%s:product:%s:amount" % (sale_id, product["id"]), product["amount"])
            database.decr("product:%s:amount" % product["id"], amount=product["amount"])
        database.set("sale:%s:client" % sale_id, client)
        database.set("sale:%s:sale_term" % sale_id, sale_term)
        database.set("sale:%s:initial_date" % sale_id, initial_date)
        database.set("sale:%s:times" % sale_id, times)
        self.redirect("/sales")


class ViewSaleHandler(BaseHandler):

    @authenticated
    def get(self):
        user_profiles = database.lrange("user:%s:profiles" % self.current_user, 0, -1)
        if "seller" not in user_profiles:
            self.redirect("/")
            return
        sale_id = self.get_argument("sale_id")
        sale = {
            "client": database.get("sale:%s:client" % sale_id),
            "sale_term": database.get("sale:%s:sale_term" % sale_id),
            "initial_date": database.get("sale:%s:initial_date" % sale_id),
            "times": database.get("sale:%s:times" % sale_id),
            "products": list(),
        }
        total = 0
        for key in database.keys("sale:%s:product:*:amount" % sale_id):
            product_id = key.split(":")[3]
            name = database.get("product:%s:name" % product_id)
            amount = database.get(key)
            price = database.get("product:%s:price" % product_id)
            partial = float(price) * float(amount)
            sale["products"].append({
                "name": name,
                "amount": amount,
                "price": ("R$ %0.2f" % float(price)).replace(".", ","),
                "partial": ("R$ %0.2f" % float(partial)).replace(".", ","),
            })
            total += partial
        sale["total"] = ("R$ %0.2f" % total).replace(".", ",")
        self.render("sale.html", sale=sale)


class RemoveSaleHandler(BaseHandler):

    @authenticated
    def get(self):
        user_profiles = database.lrange("user:%s:profiles" % self.current_user, 0, -1)
        if "seller" not in user_profiles:
            self.redirect("/")
            return
        sale_id = self.get_argument("sale_id")
        for key in database.keys("sale:%s:*" % sale_id):
            database.delete(key)
        self.redirect("/sales")


class ReportsHandler(BaseHandler):

    @authenticated
    def get(self):
        user_profiles = database.lrange("user:%s:profiles" % self.current_user, 0, -1)
        if "admin" not in user_profiles:
            self.redirect("/")
            return
        self.render("reports.html")


class BestClientHandler(BaseHandler):

    @authenticated
    def get(self):
        user_profiles = database.lrange("user:%s:profiles" % self.current_user, 0, -1)
        if "admin" not in user_profiles:
            self.redirect("/")
            return
        clients = list()
        for key in database.keys("sale:*:client"):
            client_name = database.get(key)
            if client_name not in map(lambda client: client["complete_name"], clients):
                clients.append({
                    "complete_name": client_name,
                    "sales": 0,
                })
            client = filter(lambda client: client["complete_name"] == client_name, clients)[0]
            client["sales"] += 1
        self.render("best_client.html", clients=clients)


class RedirectProtocolHandler(RequestHandler):

    def get(self):
        domain = self.request.host.split(":")[0]
        self.redirect("https://%s:8443/" % domain)


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
    (r"/sales", SalesHandler),
    (r"/register_sale", RegisterSaleHandler),
    (r"/sale", ViewSaleHandler),
    (r"/remove_sale", RemoveSaleHandler),
    (r"/reports", ReportsHandler),
    (r"/reports/best_client", BestClientHandler),
    (r"/jquery_ui/(.*)", StaticFileHandler, {"path": "./external_modules/jquery_ui"}),
    (r"/font-awesome-4.3.0/(.*)", StaticFileHandler, {"path": "./external_modules/font-awesome-4.3.0"}),
    (r"/(.*\.css)", StaticFileHandler, {"path": "./www/styles"}),
    (r"/(.*\.js)", StaticFileHandler, {"path": "./www/scripts"}),
    (r"/(.*\.png)", StaticFileHandler, {"path": "./www/images"}),
], **settings)
redirect_protocol = Application([
    (r"/.*", RedirectProtocolHandler),
])
database = Redis()
databases = dict(map(lambda line: line.strip("\n").split(":"), open("databases.dat").readlines()))

if __name__ == "__main__":
    locale.load_translations("./locales")
    redirect_protocol.listen(8000)
    https_server = HTTPServer(application, ssl_options={
        "certfile": "./certificate/carbono.crt",
        "keyfile": "./certificate/carbono.pem",
    })
    
    https_server.listen(8443)
    IOLoop.instance().start()
    

