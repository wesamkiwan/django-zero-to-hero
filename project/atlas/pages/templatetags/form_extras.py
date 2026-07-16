from django import template

register = template.Library()


@register.filter(name="add_class")
def add_class(field, css_class):
    """Usage: {{ form.name|add_class:"form-control" }}

    Lets any form field pick up a Bootstrap class without editing every
    Form's widgets by hand, and without a custom form-rendering template
    tag per field — works on any BoundField, from any form, anywhere.
    """
    return field.as_widget(attrs={"class": css_class})


@register.filter
def widget_type(field):
    """Usage: {% if field|widget_type == "Select" %}

    Returns the widget's class name (e.g. "Select", "CheckboxInput",
    "Textarea") so a template can pick the right Bootstrap class per field
    type. Done as a filter (plain Python) rather than template-side
    attribute access because Django's template language deliberately
    refuses to look up any attribute starting with an underscore —
    including "__class__" — so "field.field.widget.__class__.__name__"
    can't be written directly in a template at all.
    """
    return field.field.widget.__class__.__name__
