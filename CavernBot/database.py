from peewee import MySQLDatabase
from peewee import Model, Proxy

import yaml

REGISTERED_MODELS = []

with open('config.yaml', 'r') as f:
    config = yaml.load(f, Loader=yaml.UnsafeLoader)

bot_db = MySQLDatabase(config['database']['database_name'], user=config['database']['username'],
                                    password=config['database']['password'],
                                    host=config['database']['ip'], port=config['database']['port'])


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

