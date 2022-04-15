from datetime import datetime

from peewee import IntegerField, BigIntegerField, TextField, DateTimeField

from CavernBot.database import Base


@Base.register
class Ticket(Base):
    class Meta:
        table_name = 'tickets'

    initial_ticket_user = BigIntegerField()
    ticket_channel_id = BigIntegerField()
    initial_assigned_moderator = BigIntegerField()
    additional_users = TextField()
    additional_moderators = TextField()
    created_at = DateTimeField(default=datetime.utcnow)
    closed_at = DateTimeField()
    ticket_issue = TextField()
    ticket_category = IntegerField(default=0)
