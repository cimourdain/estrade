def get_exception(instance):
    """
    Method to find current class Exception
    :param instance: instance of a classe having an exception defined in estrade.classes.exception
    :return: <(Class)Exception>
    """
    module = __import__('estrade.classes.exceptions', fromlist=['estrade.classes.exceptions'])
    class_name = '{}Exception'.format(instance.__class__.__name__)
    return getattr(module, class_name)
