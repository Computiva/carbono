from getpass import getpass
from md5 import md5
from argparse import ArgumentParser

from redis import Redis

def main():
    arguments_parser = ArgumentParser(description="Create admin user.")
    arguments_parser.add_argument("--db", default=0, type=int, help="database number")
    arguments = arguments_parser.parse_args()
    database_number = vars(arguments)["db"]
    print("Enter your password to create an admin user.")
    database = Redis(db=database_number)
    database.set("user:admin:password", md5(getpass()).hexdigest())
    database.delete("user:admin:profiles")
    database.rpush("user:admin:profiles", "admin")

if __name__ == "__main__":
    main()
