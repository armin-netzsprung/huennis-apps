from django import template

register = template.Library()

@register.filter
def count_slashes(value):
    return value.count('/')

@register.filter
def multiply(value, arg):
    return int(value) * int(arg)

@register.filter
def split_last_part(value):
    return value.split('/')[-1]
