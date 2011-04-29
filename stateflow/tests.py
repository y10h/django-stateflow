from unittest import TestCase
from django.db import models
from django import forms
from stateflow.stateclass import DjangoState, DjangoTransition, Flow, TransitionFailedError, IncorrectStateError
from stateflow.statefields import StateFlowField, StateWidget

class StatefulObject(object):
    state = None

    def __init__(self):
        self.state = State1

#States
class State1(DjangoState):
    pass

class State2(DjangoState):
    pass

class State3(DjangoState):
    pass

#Transitions
class StateTransition(DjangoTransition):
    abstract = True
    
    @classmethod
    def apply(cls, obj, *args, **kwargs):
        if cls not in obj.state.forward_transitions:
            raise IncorrectStateError("Cannot apply transition %s for state %s" %
                             (cls, obj.state))
        if cls not in obj.state.forward_allowed_transitions(kwargs.get('roles', [])):
            raise TransitionFailedError("Cannot apply transition %s for state %s because of insufficient privileges" %
                             (cls, obj.state))
        obj.state = cls.outcome


class State1ToState2(StateTransition):
    income = [State1]
    outcome = State2
    permissions = ['writer', 'owner']

class State12ToState3(StateTransition):
    income = [State1, State2]
    outcome = State3
    permissions = ['owner']

class State3ToState1(StateTransition):
    income = [State3]
    outcome = State1
    permissions = ['owner']
    forward = False

#flow
class StateFlow(Flow):
    states = [State1, State2, State3]
    transitions = [State1ToState2, State12ToState3]
    initial_state = State1

#abstract model with StateFlowField
class StateModel(models.Model):
    state = StateFlowField(flow=StateFlow)

    class Meta():
        abstract=True

#form with StateWidget
class StateModelForm(forms.ModelForm):
    class Meta():
        model = StateModel

class TransitionTest(TestCase):

    def test_forward(self):
        obj = StatefulObject()
        self.assertEquals(obj.state, State1)

        State1ToState2.apply(obj, roles=['owner'])
        self.assertEquals(obj.state, State2)


    def test_wrong_apply(self):
        obj = StatefulObject()
        self.assertEquals(obj.state, State1)

        State12ToState3.apply(obj, roles=['owner'])
        self.assertEquals(obj.state, State3)

        self.assertRaises(IncorrectStateError,
                          State12ToState3.apply, obj, roles=['owner'])

    def test_permissions(self):
        obj = StatefulObject()
        self.assertEquals(obj.state, State1)

        State1ToState2.apply(obj, roles=['writer'])
        self.assertEquals(obj.state, State2)

        self.assertRaises(TransitionFailedError,
                          State12ToState3.apply, obj, roles=['writer'])

    def test_backward(self):
        obj = StatefulObject()
        self.assertEquals(obj.state, State1)

        State12ToState3.apply(obj, roles=['owner'])
        self.assertEquals(obj.state, State3)

        State3ToState1.apply(obj, roles=['owner'])
        self.assertEquals(obj.state, State1)

class StateFieldTest(TestCase):
    def test_form(self):
        form = StateModelForm(instance=StateModel(state=State2))

        self.assertTrue(isinstance(form.fields['state'].widget, StateWidget))
        self.assertEquals(len(form.fields['state'].choices),
                          len(StateFlow.states) + 1)
