from peewee import IntegerField, BigIntegerField, TextField, DateTimeField
from datetime import datetime

from CavernBot.database import Base


@Base.register
class Suggestion(Base):
    class Meta:
        table_name = 'suggestions'

    user_id = BigIntegerField()
    area = TextField()
    description = TextField()
    type = IntegerField(default=0)
    approving_moderator = BigIntegerField(null=True)
    upvotes = IntegerField(default=0)
    downvotes = IntegerField(default=0)
    created_at = DateTimeField(default=datetime.utcnow)
