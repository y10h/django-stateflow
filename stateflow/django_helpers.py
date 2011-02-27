from django.db import models
from django import forms

from stateflow import Status, Action

class DjangoItem(object):
    """Stores common methods of DjanoStatus and DjangoAction"""

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
        return [subclass for subclass in cls._subclasses \
                if subclass.get_value() is not None]

    @classmethod
    def choices(cls):
        return [item.as_tuple() for item in cls.all()]

    @classmethod
    def get(cls, value, default=None):
        """Finds a status by it's value"""
        for item in cls._subclasses:
            if item.get_value() == value:
                return item
        return default



class DjangoStatus(Status, DjangoItem):

    def __str__(self):
        # We need to keep this instance method in order to solve a specific
        # problem with Django templates.
        # When django template variable resolver encounters a callable it 
        # always tries to call it. And since class is a callable (and call to
        # it returns a new instance), we end up having instances, not classes
        # rendered in the template
        return str(self.__class__)

    @classmethod
    def next_allowed_actions(cls, roles):
        return [action for action in cls.next_actions \
                if set(action.permissions) & set(roles)]

    @classmethod
    def next_statuses(cls):
        return [action.outcome for action in cls.next_actions \
                if action.forward]


    @classmethod
    def all_next_statuses(cls):
        #TODO: Capture possible recursion in case of wrong 'forward' value
        def get_statuses(status, lst):
            lst.add(status)
            [get_statuses(st, lst) for st in status.next_statuses()]
        result = set([])
        get_statuses(cls, result)
        return list(result)


class IncorrectStatusError(ValueError):
    pass

class ActionFailedError(Exception):
    pass


class AdminAction(object):

    def __init__(self, action):
        self.action = action
        self.short_description = '%s selected' % action
        self.__name__ = str(action)

    def __call__(self, modeladmin, request, queryset):
        for obj in queryset:
            self.action.apply(obj)


class DjangoAction(Action, DjangoItem): 

    abstract = True #This action isn not the part of workflow

    # By default actions are considered 'forward', i.e. 
    # workflow doesn't return to previous status
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
        return [AdminAction(action) for action in cls.all()]


class NoStatus(DjangoStatus):
    value = None
    next_actions = []


class StatusWidget(forms.Select):

    def render_options(self, choices, selected_choices):
        from itertools import chain
        from django.utils.encoding import force_unicode
        from django.utils.html import escape, conditional_escape
        def render_option(option_value, option_label):
            option_value = force_unicode(option_value)
            selected_html = (option_value in selected_choices) and u' selected="selected"' or ''
            return u'<option value="%s"%s>%s</option>' % (
                escape(option_value), selected_html,
                conditional_escape(force_unicode(option_label)))
        # Normalize to strings.
        selected_choices = [v.get_value() for v in selected_choices if isinstance(v, DjangoItem)]
        selected_choices = set([force_unicode(v) for v in selected_choices])
        output = []
        for option_value, option_label in chain(self.choices, choices):
            if isinstance(option_label, (list, tuple)):
                output.append(u'<optgroup label="%s">' % escape(force_unicode(option_value)))
                for option in option_label:
                    output.append(render_option(*option))
                output.append(u'</optgroup>')
            else:
                output.append(render_option(option_value, option_label))
        return u'\n'.join(output)


class StatusField(models.Field):

    def __init__(self, verbose_name=None, name=None, status_class=NoStatus, **kwargs):
        self.status_class = status_class
        models.Field.__init__(self, verbose_name, name, **kwargs)


    __metaclass__ = models.SubfieldBase

    def get_internal_type(self):
        return "CharField"

    def get_db_prep_value(self, value):
        if value is None:
            return None
        elif isinstance(value, type) and issubclass(value, DjangoStatus):
            return value.get_value()
        else:
            return str(value)

    def to_python(self, value):
        if isinstance(value, type) and issubclass(value, DjangoStatus):
            return value
        return self.status_class.get(value, NoStatus)


    def value_to_string(self, obj):
        """
        Returns a string value of this field from the passed obj.
        This is used by the serialization framework.
        """
        return self._get_val_from_obj(obj).get_value()

    def formfield(self, **kwargs):
        choices = [(None,'----')] + self.status_class.choices()
        return forms.ChoiceField(choices=choices, widget=StatusWidget)

    def south_field_triple(self):
        """Returns a suitable description of this field for South."""
        from south.modelsinspector import introspector
        field_class = self.__class__.__module__ + '.' + self.__class__.__name__
        args, kwargs = introspector(self)
        return (field_class, args, kwargs)
