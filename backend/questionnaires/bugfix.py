"""
This module is a work around the issue of django-jsonform not handling
nullable integers correctly. It provides a custom JSONFormField that
overrides the to_python method to cast nullable integers properly.

See: https://github.com/bhch/django-jsonform/issues/192
"""

from django_jsonform.forms.fields import JSONFormField
from django_jsonform.models.fields import JSONField


class DocumentJSONFormField(JSONFormField):
    def __init__(self, *args, schema=None, **kwargs):
        super().__init__(*args, schema=schema, **kwargs)
        self.schema = schema
        
    def to_python(self, value):
        value = super().to_python(value)
        value = self._cast_nullable_integers(value, self.schema, self.schema)
        return value

    def _cast_nullable_integers(self, data, schema, root_schema):
        if isinstance(schema, dict):
            # Handle $ref
            if "$ref" in schema:
                ref_path = schema["$ref"]
                # Only supports local refs like "#/$defs/question"
                if ref_path.startswith("#/"):
                    parts = ref_path.lstrip("#/").split("/")
                    ref = root_schema
                    for part in parts:
                        ref = ref.get(part)
                    if ref is not None:
                        return self._cast_nullable_integers(data, ref, root_schema)
            if schema.get("type") == ["integer", "null"]:
                if data is None:
                    return None
                if isinstance(data, str) and data.isdigit():
                    return int(data)
            if schema.get("type") == "object" and "properties" in schema:
                return {
                    k: self._cast_nullable_integers(data.get(k), v, root_schema)
                    for k, v in schema["properties"].items()
                    if k in data
                }
            if schema.get("type") == "array" and "items" in schema:
                return [
                    self._cast_nullable_integers(item, schema["items"], root_schema)
                    for item in (data or [])
                ]
        return data


class DocumentJSONField(JSONField):
    def formfield(self, **kwargs):
        defaults = {"form_class": DocumentJSONFormField}
        defaults.update(kwargs)
        return super().formfield(**defaults)
