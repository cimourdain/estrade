from typing import Optional

from estrade.enums import TransactionStatus


class TransactionMixin:
    def __init__(self, status: Optional[TransactionStatus] = TransactionStatus.PENDING):
        self.status = status  # TODO validate status in Enum
