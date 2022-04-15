from peewee import IntegerField, BigIntegerField, TextField, DateTimeField, BooleanField
from datetime import datetime

from CavernBot.database import Base


@Base.register
class Suggestion(Base):
    class Meta:
        table_name = 'suggestions'

    user_id = BigIntegerField()
    message_id = BigIntegerField()
    area = TextField()
    description = TextField()
    example = TextField(null=True)
    type = IntegerField(default=0)
    approving_moderator = BigIntegerField(null=True)
    upvotes = IntegerField(default=0)
    downvotes = IntegerField(default=0)
    created_at = DateTimeField(default=datetime.utcnow)
    forced = BooleanField(default=False)
    forced_by = BigIntegerField(null=True)


@Base.register
class SuggestionVote(Base):
    class Meta:
        table_name = 'suggestion_votes'

    suggestion_id = BigIntegerField()
    user_id = BigIntegerField()
    vote = IntegerField(default=0)
