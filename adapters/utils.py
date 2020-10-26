from datetime import datetime


def get_timestamp(timestamp):
    return timestamp.strftime("%s") if isinstance(timestamp, datetime) else timestamp
