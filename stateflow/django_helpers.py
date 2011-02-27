from django.db import models
from django import forms

from stateflow import State, Transition

class DjangoItem(object):
    """Stores common methods of DjanoState and DjangoTransition"""

    @classmethod
    def get_value(cls):
        try:
            return getattr(cls, 'value')
        except AttributeError:
            return cls.__name__.upper()

    @classmethod
    def get_title(cls):
        title = getattr(cls, 'title', None)
        return title or cls.__name__

    @classmethod
    def as_tuple(cls):
        return cls.get_value(), cls.get_title()

    @classmethod
    def as_sql(cls):
        return '%s', (cls.get_value(),)

    @classmethod
    def all(cls):
        return [subclass for subclass in cls._subclasses
                if subclass.get_value() is not None]

    @classmethod
    def choices(cls):
        return [item.as_tuple() for item in cls.all()]

    @classmethod
    def get(cls, value, default=None):
        """Finds a state by it's value"""
        for item in cls._subclasses:
            if item.get_value() == value:
                return item
        return default



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
    def admin_actions(cls):
        return [AdminAction(trans) for trans in cls.all()]


class NoState(DjangoState):
    value = None
    forward_transitions = []


class StateWidget(forms.Select):

    def render_options(self, choices, selected_choices):
        from itertools import chain
        from django.utils.encoding import force_unicode
        from django.utils.html import escape, conditional_escape
        def render_option(option_value, option_label):
            option_value = force_unicode(option_value)
            selected_html = (option_value in selected_choices) \
                and u' selected="selected"' or ''
            return u'<option value="%s"%s>%s</option>' % (
                escape(option_value), selected_html,
                conditional_escape(force_unicode(option_label)))
        # Normalize to strings.
        selected_choices = [
            v.get_value()
            for v in selected_choices if isinstance(v, DjangoItem)]
        selected_choices = set([force_unicode(v) for v in selected_choices])
        output = []
        for option_value, option_label in chain(self.choices, choices):
            if isinstance(option_label, (list, tuple)):
                output.append(u'<optgroup label="%s">' %
                              escape(force_unicode(option_value)))
                for option in option_label:
                    output.append(render_option(*option))
                output.append(u'</optgroup>')
            else:
                output.append(render_option(option_value, option_label))
        return u'\n'.join(output)


class StateField(models.Field):

    def __init__(self, verbose_name=None, name=None,
                 state_class=NoState, **kwargs):
        self.state_class = state_class
        models.Field.__init__(self, verbose_name, name, **kwargs)


    __metaclass__ = models.SubfieldBase

    def get_internal_type(self):
        return "CharField"

    def get_db_prep_value(self, value):
        if value is None:
            return None
        elif isinstance(value, type) and issubclass(value, DjangoState):
            return value.get_value()
        else:
            return str(value)

    def to_python(self, value):
        if isinstance(value, type) and issubclass(value, DjangoState):
            return value
        return self.state_class.get(value, NoState)


    def value_to_string(self, obj):
        """
        Returns a string value of this field from the passed obj.
        This is used by the serialization framework.
        """
        return self._get_val_from_obj(obj).get_value()

    def formfield(self, **kwargs):
        choices = [(None,'----')] + self.state_class.choices()
        return forms.ChoiceField(choices=choices, widget=StateWidget)

    def south_field_triple(self):
        """Returns a suitable description of this field for South."""
        from south.modelsinspector import introspector
        field_class = self.__class__.__module__ + '.' + self.__class__.__name__
        args, kwargs = introspector(self)
        return (field_class, args, kwargs)
