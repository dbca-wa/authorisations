import json
import base64

from django import template

register = template.Library()


@register.filter
def b64encode(value):
    if isinstance(value, (list, dict)):
        value = json.dumps(value)
    
    if isinstance(value, bytes):
        return base64.b64encode(value).decode("utf-8")
    elif isinstance(value, str):
        return base64.b64encode(value.encode("utf-8")).decode("utf-8")
    
    raise TypeError("Value must be a string or bytes to encode in base64.")
