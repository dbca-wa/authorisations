from api.forms import JsonSchemaModelForm

from .schema import get_answers_schema


class ApplicationForm(JsonSchemaModelForm):
    _schema = get_answers_schema()
