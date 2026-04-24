from django import template

register = template.Library()


@register.filter
def phone_hyphen(value):
    if not value:
        return value
    digits = "".join(ch for ch in str(value) if ch.isdigit())
    if len(digits) == 11:
        return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
    return value
