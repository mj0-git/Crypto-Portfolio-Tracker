from django import template

register = template.Library()

@register.simple_tag
def define(val=None):
  return val
  
@register.filter(name='add_comma')
def add_comma(value):
    return "{:,}".format(value)

