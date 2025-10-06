import os

from dotenv import load_dotenv
from peewee import MySQLDatabase
from peewee import Model, Proxy

REGISTERED_MODELS = []

load_dotenv()

bot_db = MySQLDatabase(os.getenv("DB_DATABASE"),
                       user=os.getenv("DB_USERNAME"),
                       password=os.getenv("DB_PASSWORD"),
                       host=os.getenv("DB_HOST"),
                       port=int(os.getenv("DB_PORT"))
                   )


class Base(Model):
    class Meta:
        database = bot_db

    @staticmethod
    def register(cls):
        cls.create_table(True)
        if hasattr(cls, 'SQL'):
            bot_db.execute_sql(cls.SQL)

        REGISTERED_MODELS.append(cls)
        return cls

