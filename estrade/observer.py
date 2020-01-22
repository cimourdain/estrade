import logging

logger = logging.getLogger(__name__)


class Observable:
    """
    Class used to implement observer pattern.
    """

    def __init__(self):
        """
        When instanciated, an observer class create an empty dict of callbacks.
        """
        logger.debug('init %s as observable' % self.__class__.__name__)
        self.callbacks = {}

    def subscribe(self, event_name, callback):
        """
        When another object subscribe to this object, it define the name of event and the callback function
        :param event_name: <str>
        :param callback: function name
        :return:
        """
        logger.debug('Add callback %s on to event %s fired by %s' % (callback, event_name, self.__class__.__name__))
        if event_name not in self.callbacks:
            self.callbacks[event_name] = [callback]
        elif callback not in self.callbacks[event_name]:
            self.callbacks[event_name].append(callback)
        else:
            logger.warning('callback %s is attached twice to event %s' % (callback, event_name))

    def fire(self, event_name, *args, **kwargs):
        """
        When an event occurs, this function is called with the event name and call all defined callbacks
        with args/kwargs.
        :param event_name: <str>
        :return:
        """
        logger.debug('fire event %s from %s' % (event_name, self.__class__.__name__))
        if not self.callbacks.get(event_name):
            logger.debug('Event %s is not subscribed by any object, it will not call any callback' % event_name)
        else:
            for callback in self.callbacks.get(event_name, []):
                logger.debug('Call callback %s' % callback)
                callback(*args, **kwargs)
