from django.db import models
from django import forms
from django.utils.importlib import import_module

from stateclass import DjangoState, Flow



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


def load_flow(flow_path):
    dot = flow_path.rindex('.')
    mod_name, cls_name = flow_path[:dot], flow_path[dot+1:]
    mod = import_module(mod_name)
    flow = getattr(mod, cls_name)
    return flow


def resolve_flow(flow_name):
    try:
        flow_is_cls = issubclass(flow_name, Flow)
    except:
        flow_is_cls = False
    if flow_is_cls:
        return flow_name, str(flow_name)
    else:
        return load_flow(flow_name), flow_name


class StateFlowField(models.Field):

    __metaclass__ = models.SubfieldBase

    def __init__(self, verbose_name=None, name=None,
                 flow=None, **kwargs):
        if flow is None:
            raise ValueError("StateFlowField need to have defined flow")
        self.flow, self.flow_path = resolve_flow(flow)
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


# Add suport of StateFlowField for South
def add_south_introspector_rules():
    from south.modelsinspector import add_introspection_rules

    rules = [
        (
            (StateFlowField, ),
            [],
            {
                "flow": ["flow_path", {}],
            }
        ),
    ]

    add_introspection_rules(rules, ["^stateflow\.statefields"])

try:
    import south
except ImportError:
    pass
else:
    add_south_introspector_rules()
