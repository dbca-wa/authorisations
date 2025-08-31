from api.forms import JsonSchemaModelForm

from .schema import get_questionnaire_schema


class QuestionnaireForm(JsonSchemaModelForm):
    _schema = get_questionnaire_schema()
