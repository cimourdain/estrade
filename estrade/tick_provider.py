import logging
from typing import Generator, List, Optional

from estrade import Epic, Tick


logger = logging.getLogger(__name__)


class BaseTickProvider:
    """
    Abstract representation of a Tick Generator.

    Attributes:
        epics (List[estrade.epic.Epic]): list of [`Epics`][estrade.epic.Epic]
            that can be used to generate [`Ticks`][estrade.tick.Tick]
            in the `run` method.
    """

    def __init__(self, epics: List[Epic]):
        """
        Define a [`Tick`][estrade.tick.Tick] generator.

        Arguments:
            epics: A list of Epic instances

        """
        # store epics in a dict with ref as key
        self.epics = {}
        for epic in epics:
            self.epics[epic.ref] = epic

    def get_epic_by_ref(self, ref: str) -> Optional[Epic]:
        """
        Get an [`Epic`][estrade.epic.Epic] by its reference.

        Arguments:
            ref: reference of [`Epic`][estrade.epic.Epic]

        Returns:
            [`Epic`][estrade.epic.Epic] instance
        """
        return self.epics.get(ref)

    def run(self) -> Generator[Tick, None, None]:
        """
        Run the tick provider.

        Method to be implemented to generate [`Tick`][estrade.tick.Tick] objects and
        attach them to the corresponding Epic.
        """
        raise NotImplementedError()
