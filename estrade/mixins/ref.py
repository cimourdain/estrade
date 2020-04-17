from typing import Optional
from uuid import uuid4


class RefMixin:
    def __init__(self, ref: Optional[str] = None):
        """
        Handle reference of an object.

        Attributes:
            ref: reference of the instance.

        """
        self.ref = ref  # type: ignore

    @property
    def ref(self) -> str:
        """
        Return ref of current instance.

        Returns:
            reference of current instance.
        """
        return self._ref

    @ref.setter
    def ref(self, ref: Optional[str] = None) -> None:
        """
        Set current instance reference.

        Arguments:
            ref: predefined reference name
        """
        self._ref = ref or str(uuid4())[:5]
