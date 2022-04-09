from peewee import IntegerField, BigIntegerField, TextField, DateTimeField
from datetime import datetime

from CavernBot.database import CavernBot


class Suggestion(CavernBot):
    class Meta:
        table_name = 'suggestions'

    user_id = BigIntegerField()
    area = TextField()
    description = TextField()
    approving_moderator = BigIntegerField(null=True)
    votes = IntegerField()
    created_at = DateTimeField(default=datetime.utcnow)

    @classmethod
    def create_suggestion(cls, event, member, area, description):
        pass
