from django import template
from django.template import Template, Context
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag(takes_context=True)
def render_flatpage(context, page):
    """
    Renders a flatpage, processing Django template tags like {% now "Y" %}.
    ENV variable substitution (${ENV.x}) is handled client-side by JavaScript.
    """
    try:
        rendered_content = Template(page.content).render(Context({}))
    except Exception:
        rendered_content = page.content

    return mark_safe(rendered_content)
