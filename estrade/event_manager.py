# import logging
# import threading
#
# from typing import Dict, Callable, List, Any, Tuple
#
# logger = logging.getLogger(__name__)
#
#
# class EventManager:
#
#     INSTANCE = None
#
#     class __EventManager:
#         def __init__(self) -> None:
#             self.callbacks: Dict[str, List[Callable]]= {}
#
#         def register(self, event_name, callback, *args, **kwargs) -> None:
#             if not self.callbacks.get(event_name):
#                 self.callbacks[event_name]: List[Dict[str, Any]] = []
#
#             callback_dict = {
#                 "callback": callback,
#                 "default_args": args,
#                 "default_kwargs": kwargs,
#             }
#             self.callbacks[event_name].append(callback_dict)
#
#         @staticmethod
#         def merge_args(call_args, default_args) -> Tuple[Any]:
#             target_args = []
#             max_args = max(len(call_args), len(default_args))
#             for i in range(0, max_args):
#                 try:
#                     arg = call_args[i]
#                 except KeyError:
#                     arg = default_args[i]
#                 target_args.append(arg)
#
#             return tuple(target_args)
#
#         @staticmethod
#         def merge_kwargs(call_kwargs, default_kwargs) -> Dict[str, Any]:
#             target_kwargs = default_kwargs.copy()
#             target_kwargs.update(call_kwargs)
#             return target_kwargs
#
#         def execute_callback_in_thread(self, event_name, *args, **kwargs):
#             callbacks = self.callbacks.get(event_name)
#             if not callbacks:
#                 logger.debug("No callback registered for %s", event_name)
#                 return
#
#             for callback_dict in callbacks:
#                 logger.debug("call %s" % callback_dict)
#
#                 args = self.merge_args(args, callback_dict["default_args"])
#
#                 kwargs = self.merge_kwargs(kwargs, callback_dict["default_kwargs"])
#                 callback_dict["callback"](*args, **kwargs)
#
#         def fire(self, event_name, *args, **kwargs) -> None:
#             thr = threading.Thread(
#                 target=self.execute_callback_in_thread,
#                 args=(event_name,) + args,
#                 kwargs=kwargs,
#             )
#             thr.start()
#
#         def subscribe(self, event_name, *args, **kwargs):
#             def decorator(func):
#                 def wrapped(*call_args, **call_kwargs):
#                     return func(*call_args, **call_kwargs)
#
#                 self.register(event_name, wrapped, *args, **kwargs)
#                 return wrapped
#
#             return decorator
#
#     def __new__(cls) -> "__EventManager":
#         if not EventManager.INSTANCE:
#             instance = EventManager.__EventManager()
#             EventManager.INSTANCE = instance
#         return EventManager.INSTANCE
#
#
# event_manager = EventManager()
