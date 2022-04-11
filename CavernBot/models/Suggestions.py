from peewee import IntegerField, BigIntegerField, TextField, DateTimeField
from datetime import datetime

from CavernBot.database import Base

import json

#
# class JSONField(TextField):
#     """
#     Class to "fake" a JSON field with a text field. Not efficient but works nicely
#     """
#
#     def db_value(self, value):
#         """Convert the python value for storage in the database."""
#         return value if value is None else json.dumps(value)
#
#     def python_value(self, value):
#         """Convert the database value to a pythonic value."""
#         return value if value is None else json.loads(value)


@Base.register
class Suggestion(Base):
    class Meta:
        table_name = 'suggestions'

    user_id = BigIntegerField()
    message_id = BigIntegerField()
    area = TextField()
    description = TextField()
    type = IntegerField(default=0)
    approving_moderator = BigIntegerField(null=True)
    upvotes = IntegerField(default=0)
    downvotes = IntegerField(default=0)
    created_at = DateTimeField(default=datetime.utcnow)
    # votes = JSONField()
