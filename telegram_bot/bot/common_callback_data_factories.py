import re
from aiogram.filters.callback_data import CallbackData


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

class PaginationClickSpecializations(PaginationClick, CallbackData, prefix="specializations"):
    """створює колбек строку для натискання на кнопку спеціальностей"""
    pass

class PaginationClickDoctors(PaginationClick, CallbackData, prefix="doctors"):
    """створює колбек строку для натискання на кнопку доктори"""
    pass

class PaginationClickSlots(PaginationClick, CallbackData, prefix="slots"):
    """створює колбек строку для показу слотів"""
    pass
