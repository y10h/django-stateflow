#============================
# Generic workflow mechanism
#============================

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

    
class StatusMetaclass(RegistryMetaclass):

    def __init__(cls, name, bases, dict):
        super(StatusMetaclass, cls).__init__(name, bases, dict)
        abstract = dict.pop('abstract', False)
        if not abstract:
            cls.next_actions = []
            cls.prev_actions = []
    
    # TODO: This method don't belong to 'general' part
    # But it's here because of metaclass conflict.
    # Something should be done about it
    def __str__(cls):
        return cls.get_title()

    def __repr__(cls):
        return "<Status: '%s'>" % cls.get_title()

class ActionMetaclass(RegistryMetaclass):

    def __init__(cls, name, bases, dict):
        super(ActionMetaclass, cls).__init__(name, bases, dict)
        abstract = dict.pop('abstract', False)
        if not abstract:
            for klass in dict['income']:
                next_actions = getattr(klass, 'next_actions')
                next_actions.append(cls)
            getattr(klass, 'prev_actions').append(cls)

    def __str__(cls):
        return cls.get_title()

    def __repr__(cls):
        return "<Action: '%s'>" % cls.get_title()



class Status(object):

    __metaclass__ = StatusMetaclass

    abstract = True


class Action(object):
    
    __metaclass__ = ActionMetaclass

    abstract = True


    @classmethod
    def apply(cls, obj, *args, **kwargs):
        raise NotImplementedError("Apply method should be defined in subclasses")

    def __init__(self, obj=None):
        self.obj = obj

    def __call__(self, *args, **kwargs):
        return self.__class__.apply(self.obj, *args, **kwargs)

    def __get__(self, instance, owner=None):
        #TODO: Make sure that all situations are handled properly
        if owner is not None:
            return self.__class__(instance)
        return self 


