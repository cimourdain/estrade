import inspect


def post_build(func):
    def wrapper(*args, **kwargs):
        func(*args, **kwargs)

    wrapper.__decorator__ = post_build
    return wrapper


class Factory:
    class Meta:
        model = None

    def __init__(self):
        pass

    @classmethod
    def get_default_args(cls):
        default_args = {}
        post_load_func = []
        class_args = inspect.getmembers(cls)
        for arg in class_args:
            arg_key, arg_value = arg
            if (
                not arg_key.startswith("__")
                and arg_key != "Meta"
                and arg_key != "get_default_args"
            ):
                if callable(arg_value):
                    if getattr(arg_value, "__decorator__", None) == post_build:
                        post_load_func.append(arg_value)
                    else:
                        default_args[arg_key] = arg_value()
                else:
                    default_args[arg_key] = arg_value
        return default_args, post_load_func

    def __new__(cls, *args, **kwargs):
        build_kwargs, post_load_func = cls.get_default_args()
        build_kwargs.update(kwargs)
        build = cls.Meta.model(*args, **build_kwargs)

        for f in post_load_func:
            f(build)

        return build
