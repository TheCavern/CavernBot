from peewee import IntegerField, BigIntegerField, TextField, DateTimeField

from CavernBot.database import Base
from CavernBot.models import datetime_utc


@Base.register
class Ticket(Base):
    class Meta:
        table_name = 'tickets'

    initial_ticket_user = BigIntegerField()
    ticket_channel_id = BigIntegerField()
    initial_assigned_moderator = BigIntegerField()
    additional_users = TextField()
    additional_moderators = TextField()
    created_at = DateTimeField(default=datetime_utc)
    closed_at = DateTimeField()
    ticket_issue = TextField()
    ticket_category = IntegerField(default=0)
