from django import forms
from django_jsonform.utils import join_coords
from jsonschema import ValidationError, validate
from django_jsonform.validators import JSONSchemaValidationError

from questionnaires.serialisers import get_schema


class QuestionnaireForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["document"].widget.validate_on_submit = True
        self.fields["document"].validators = [self.document_validator]
        
    def document_validator(self, value):
        """Check value against the JSON schema
        TODO: Maybe implement multi validation error mapping (yeah nah).
        """
        try:
            validate(value, get_schema())
        except ValidationError as e:
            # Get the exact coordinate from error path
            coor: str = join_coords(*list(e.absolute_path))
            # print(f"validation error coordinate: {coor}")
            raise JSONSchemaValidationError(
                message=f"Validation error: {e.message} ({coor})",
                error_map={coor: e.message},
            )
        
        # The document is valid but is it changed?
        if self.instance.document == value:
            raise forms.ValidationError("No change detected in the document field.")
