"""
Generic workflow mechanism
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

    def __init__(self, states, transitions, initial_state):
        self.states = states
        self.transitions = transitions
        self.initial_state = initial_state

        for state in self.states:
            state.flow = self

        for transition in self.transitions:
            transition.flow = self

    def get_state(self, value=None):
        if value is None or value == '':
            return self.initial_state
        for item in self.states:
            if item.get_value() == value:
                return item
        raise ValueError('Cannot find state %r' % value)

    def state_choices(self):
        return [state.as_tuple() for state in self.states]
