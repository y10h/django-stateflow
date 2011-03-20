from django.db import models
from django import forms

from stateclass import DjangoState



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
            for v in selected_choices if isinstance(v, DjangoState)]
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



class StateFlowField(models.Field):

    __metaclass__ = models.SubfieldBase

    def __init__(self, verbose_name=None, name=None,
                 flow=None, **kwargs):
        if flow is None:
            raise ValueError("StateFlowField need to have defined flow")
        self.flow = flow
        models.Field.__init__(self, verbose_name, name, **kwargs)

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
        return self.flow.get_state(value)

    def value_to_string(self, obj):
        """
        Returns a string value of this field from the passed obj.
        This is used by the serialization framework.
        """
        return self._get_val_from_obj(obj).get_value()

    def formfield(self, **kwargs):
        choices = [(None, '----')] + self.flow.state_choices()
        return forms.ChoiceField(choices=choices, widget=StateWidget)

    def south_field_triple(self):
        """Returns a suitable description of this field for South."""
        from south.modelsinspector import introspector
        field_class = self.__class__.__module__ + '.' + self.__class__.__name__
        args, kwargs = introspector(self)
        return (field_class, args, kwargs)
