from getpass import getpass
from md5 import md5

from redis import Redis

def main():
    print("Enter you password to create a root user")
    database = Redis()
    database.set("user:admin:password", md5(getpass()).hexdigest())
    database.delete("user:admin:profiles")
    database.rpush("user:admin:profiles", "admin")

if __name__ == "__main__":
    main()
