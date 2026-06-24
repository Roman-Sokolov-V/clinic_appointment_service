import re
from aiogram.filters.callback_data import CallbackData


# class SpecClick(CallbackData, prefix="spec"):
#     spec_id: int
#     spec_name: str = ""



#
# class DocClick(CallbackData, prefix="doc"):
#     doctor_id: int
#
class SlotClick(CallbackData, prefix="slot"):
    slot_id: int
    doctor_id: int

class PaymentMethodClick(CallbackData, prefix="pay_method"):
    slot_id: int
    method: str


class PaginationClick():
    limit: int | None = None
    offset: int | None = None

    @classmethod
    def from_url(cls, next_url: str | None = None) -> 'PaginationClick':
        if not next_url:
            return cls(limit=None, offset=None)
        limit_match = re.search(r"limit=(\d+)", next_url)
        offset_match = re.search(r"offset=(\d+)", next_url)
        return cls(
            limit=int(limit_match.group(1)) if limit_match else None,
            offset=int(offset_match.group(1)) if offset_match else None
        )

class PaginationClickSpecializations(PaginationClick, CallbackData, prefix="spec"):
    pass

class PaginationClickDoctors(PaginationClick, CallbackData, prefix="doc"):
    pass

class PaginationClickSlots(PaginationClick, CallbackData, prefix="slot"):
    pass
