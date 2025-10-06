from peewee import IntegerField, BigIntegerField, TextField, DateTimeField, BooleanField, AutoField

from CavernBot.constants import SuggestionStatus
from CavernBot.database import Base
from CavernBot.models import datetime_utc


@Base.register
class Suggestion(Base):
    class Meta:
        table_name = 'suggestions'

    id = AutoField(primary_key=True)
    user_id = BigIntegerField()
    message = TextField(null=True)
    category = TextField()
    description = TextField()
    status = IntegerField(default=SuggestionStatus.PENDING)
    reviewing_moderator = BigIntegerField(null=True)
    created_at = TextField(default=datetime_utc)
    updated_at = TextField(null=True)
    updated_by = BigIntegerField(null=True)
    forced = BooleanField(default=False)
    forced_by = BigIntegerField(null=True)


@Base.register
class SuggestionVote(Base):
    class Meta:
        table_name = 'suggestion_votes'

    suggestion_id = BigIntegerField()
    user_id = BigIntegerField()
    vote = IntegerField(default=0)
