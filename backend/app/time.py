from datetime import datetime, timezone


def as_utc(value: datetime) -> datetime:
    """Treat naive datetimes as UTC and convert aware ones to UTC.

    Mongo stores datetimes in UTC. Mixed offsets would make `from` / `to`
    filters drop or include the wrong events.
    """
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
