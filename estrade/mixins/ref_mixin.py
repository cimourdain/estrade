import uuid

from estrade.mixins import get_exception


class RefMixin:
    """
    Abstract class to use as parent of clases having a reference
    """

    def __init__(self, ref):
        self.ref = ref

    @property
    def ref(self):
        return self._ref

    @ref.setter
    def ref(self, ref):
        """
        A reference is either :
            - a string provided on init
            - a string generated as <class_name>_<uuid>[:4]
        :param ref: <str>
        :return:
        """
        if ref is not None:
            if not isinstance(ref, str):
                raise get_exception(self)('Impossible to set a non string as ref')
            self._ref = ref
        else:
            self.ref = f'{self.__class__.__name__.lower()}_{str(uuid.uuid4())[:4]}'
