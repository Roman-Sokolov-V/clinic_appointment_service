import datetime

from django.utils import timezone

from clinic.models import Appointment


def get_expires_at(start: datetime) -> int:
    now_timestamp = int(timezone.now().timestamp())
    slot_start_timestamp = int(start.timestamp())
    ideal_expiry = min(slot_start_timestamp - 3600, now_timestamp + 86400)  # 1 hour  24 hour
    expires_at = max(ideal_expiry, now_timestamp + 1810)  # if ideal_expiry less than ~ 30 min add extra ~30 min
    return expires_at