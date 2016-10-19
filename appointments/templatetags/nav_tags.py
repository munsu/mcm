from django import template
from django.core.urlresolvers import reverse, NoReverseMatch


register = template.Library()

@register.simple_tag
def active_class(request, name, active_class="active"):
    try:
        path = reverse(name)
    except NoReverseMatch:
        path = name
    if request.path == path:
        return active_class
    return ''
