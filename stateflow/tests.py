from unittest import TestCase
from django.db import models
from django import forms
from stateflow import stateclass, statefields

class Article(object):

    state = None

    def __init__(self):
        self.state = New

#States
class New(stateclass.DjangoState):
    pass

class Submitted(stateclass.DjangoState):
    pass

class Approved(stateclass.DjangoState):
    pass

class Rejected(stateclass.DjangoState):
    pass

#Transitions
class StateTransition(stateclass.DjangoTransition):
    abstract = True

    @classmethod
    def apply(cls, obj, *args, **kwargs):
        if cls not in obj.state.forward_transitions:
            raise stateclass.IncorrectStateError(
                "Cannot apply transition %s for state %s" % (cls, obj.state))
        if cls not in obj.state.forward_allowed_transitions([
                kwargs.get('role')]):
            raise stateclass.TransitionFailedError(
                "Cannot apply transition %s for state %s because of "
                "insufficient privileges" % (cls, obj.state))
        obj.state = cls.outcome


class Submit(StateTransition):
    income = [New, Rejected]
    outcome = Submitted
    permissions = ['writer']

class Approve(StateTransition):
    income = [Submitted]
    outcome = Approved
    permissions = ['editor']

class Reject(StateTransition):
    income = [Submitted]
    outcome = Rejected
    permissions = ['editor']
    forward = False

# flow
class ArticleFlow(stateclass.Flow):
    states = [New, Submitted, Approved, Rejected]
    transitions = [Submit, Approve, Reject]
    initial_state = New

# abstract model with StateFlowField
class ArticleModel(models.Model):
    state = statefields.StateFlowField(flow=ArticleFlow)

    class Meta():
        abstract=True

# form with StateWidget
class ArticleModelForm(forms.ModelForm):
    class Meta():
        model = ArticleModel

class TransitionTest(TestCase):

    def test_forward(self):
        obj = Article()
        self.assertEquals(obj.state, New)

        Submit.apply(obj, role='writer')
        self.assertEquals(obj.state, Submitted)


    def test_wrong_apply(self):
        obj = Article()
        self.assertEquals(obj.state, New)

        self.assertRaises(stateclass.IncorrectStateError,
                          Reject.apply, obj, role='editor')

    def test_permissions(self):
        obj = Article()
        self.assertEquals(obj.state, New)

        Submit.apply(obj, role='writer')
        self.assertEquals(obj.state, Submitted)

        self.assertRaises(stateclass.TransitionFailedError,
                          Approve.apply, obj, role='writer')

    def test_backward(self):
        obj = Article()
        self.assertEquals(obj.state, New)

        Submit.apply(obj, role='writer')
        self.assertEquals(obj.state, Submitted)

        Reject.apply(obj, role='editor')
        self.assertEquals(obj.state, Rejected)

        Submit.apply(obj, role='writer')
        self.assertEquals(obj.state, Submitted)


class StateFieldTest(TestCase):
    def test_form(self):
        form = ArticleModelForm(instance=ArticleModel(state=Submitted))

        self.assertTrue(isinstance(form.fields['state'].widget,
                                   statefields.StateWidget))
        self.assertEquals(len(form.fields['state'].choices),
                          len(ArticleFlow.states) + 1)
