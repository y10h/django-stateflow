"""
Workflow based on Python classes
"""

class StateMetaclass(type):

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

class TransitionMetaclass(type):

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

class FlowMetaclass(type):

    def __init__(cls, name, bases, attrs):
        super(FlowMetaclass, cls).__init__(name, bases, attrs)

        for state in cls.states:
            state.flow = cls

        for transition in cls.transitions:
            transition.flow = cls

    def __str__(cls):
        return ".".join([cls.__module__, cls.__name__])



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


class Flow(object):

    __metaclass__ = FlowMetaclass

    states = []
    transitions = []
    initial_state = None


    @classmethod
    def get_state(cls, value=None):
        if value is None or value == '':
            return cls.initial_state
        for item in cls.states:
            if item.get_value() == value:
                return item
        raise ValueError('Cannot find state %r' % value)

    @classmethod
    def state_choices(self):
        return [state.as_tuple() for state in cls.states]


class DjangoItem(object):
    """Stores common methods of DjanoState and DjangoTransition"""

    @classmethod
    def get_name(cls):
        return cls.__name__

    @classmethod
    def get_value(cls):
        try:
            return getattr(cls, 'value')
        except AttributeError:
            return cls.get_name().upper()

    @classmethod
    def get_title(cls):
        title = getattr(cls, 'title', None)
        return title or cls.get_name()

    @classmethod
    def as_tuple(cls):
        return cls.get_value(), cls.get_title()

    @classmethod
    def as_sql(cls):
        return '%s', (cls.get_value(),)



class DjangoState(State, DjangoItem):

    def __str__(self):
        # We need to keep this instance method in order to solve a specific
        # problem with Django templates.
        # When django template variable resolver encounters a callable it
        # always tries to call it. And since class is a callable (and call to
        # it returns a new instance), we end up having instances, not classes
        # rendered in the template
        return str(self.__class__)


    @classmethod
    def forward_allowed_transitions(cls, roles):
        return [trans for trans in cls.forward_transitions
                if set(trans.permissions) & set(roles)]

    @classmethod
    def forward_states(cls):
        return [trans.outcome for trans in cls.forward_transitions
                if trans.forward]


    @classmethod
    def all_forward_states(cls):
        #TODO: Capture possible recursion in case of wrong 'forward' value
        def get_states(state, lst):
            lst.add(state)
            [get_states(st, lst) for st in state.forward_states()]
        result = set([])
        get_states(cls, result)
        return list(result)


class IncorrectStateError(ValueError):
    pass

class TransitionFailedError(Exception):
    pass


class AdminAction(object):

    def __init__(self, transition):
        self.transition = transition
        self.short_description = '%s selected' % transition
        self.__name__ = str(transition)

    def __call__(self, modeladmin, request, queryset):
        for obj in queryset:
            self.transition.apply(obj)


class DjangoTransition(Transition, DjangoItem):

    abstract = True # This transition is not the part of workflow

    # By default transitions are considered 'forward', i.e.
    # workflow doesn't return to previous state
    forward = True

    def __str__(self):
        # We need to keep this instance method in order to solve a specific
        # problem with Django templates.
        # When django template variable resolver encounters a callable it
        # always tries to call it. And since class is a callable (and call to
        # it returns a new instance), we end up having instances, not classes
        # rendered in the template
        return str(self.__class__)

    @classmethod
    def all(cls):
        import warnings
        warnings.warn("transition.all is deprecated, "
                      "use flow.transitions instead",
                      DeprecationWarning)
        return cls.flow.transitions

    @classmethod
    def admin_actions(cls):
        return [AdminAction(trans) for trans in cls.all()]
