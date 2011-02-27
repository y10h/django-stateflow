"""
Generic workflow mechanism
"""

class RegistryMetaclass(type):
    """
    A simple metaclass that allows class to keep a list of it's immediate
    subclasses.
    Python has __subclasses__ attribute, but it has uncertain status
    """

    def __init__(cls, name, bases, dict):
        super(RegistryMetaclass, cls).__init__(name, bases, dict)
        cls._subclasses = []
        for klass in bases:
            if hasattr(klass, '_subclasses'):
                klass._subclasses.append(cls)

    def __iter__(cls):
        return iter(cls._subclasses)


class StateMetaclass(RegistryMetaclass):

    def __init__(cls, name, bases, dict):
        super(StateMetaclass, cls).__init__(name, bases, dict)
        abstract = dict.pop('abstract', False)
        if not abstract:
            cls.forward_transitions = []
            cls.backward_transitions = []

    # TODO: This method don't belong to 'general' part
    # But it's here because of metaclass conflict.
    # Something should be done about it
    def __str__(cls):
        return cls.get_title()

    def __repr__(cls):
        return "<State: '%s'>" % cls.get_title()

class TransitionMetaclass(RegistryMetaclass):

    def __init__(cls, name, bases, dict):
        super(TransitionMetaclass, cls).__init__(name, bases, dict)
        abstract = dict.pop('abstract', False)
        if not abstract:
            for klass in dict['income']:
                forward_transitions = getattr(klass, 'forward_transitions')
                forward_transitions.append(cls)
            getattr(klass, 'backward_transitions').append(cls)

    def __str__(cls):
        return cls.get_title()

    def __repr__(cls):
        return "<Transition: '%s'>" % cls.get_title()



class State(object):

    __metaclass__ = StateMetaclass

    abstract = True


class Transition(object):

    __metaclass__ = TransitionMetaclass

    abstract = True


    @classmethod
    def apply(cls, obj, *args, **kwargs):
        raise NotImplementedError(
            "Apply method should be defined in subclasses")

    def __init__(self, obj=None):
        self.obj = obj

    def __call__(self, *args, **kwargs):
        return self.__class__.apply(self.obj, *args, **kwargs)

    def __get__(self, instance, owner=None):
        #TODO: Make sure that all situations are handled properly
        if owner is not None:
            return self.__class__(instance)
        return self

