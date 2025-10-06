from datetime import datetime, timezone


# Default passed to peewee must be a method, so using helper method to generate utc timestamp as datetime.utcnow is deprecated.
def datetime_utc():
    return datetime.now(timezone.utc).isoformat()

def iso_to_datetime(iso_string):
    return datetime.fromisoformat(iso_string)


