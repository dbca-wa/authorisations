from django import forms
from django_jsonform.utils import join_coords
from jsonschema import ValidationError, validate
from django_jsonform.validators import JSONSchemaValidationError, JSONSchemaValidator

from questionnaire.serialisers import get_schema


class QuestionnaireForm(forms.ModelForm):
    # django_jsonform validation is crap, use jsonschema directly
    # _validator = JSONSchemaValidator(schema=get_schema())
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set created_by readonly if possible
        # How do I make this readonly instead of disabled? If this is disabled, it doesn't submit in the django admin therefore None error even though with an initial value assigned.
        # if 'created_by' in self.fields:
        #     self.fields['created_by'].disabled = True
        #     # self.fields['created_by'].widget.attrs['readonly'] = True

        self.fields["document"].widget.validate_on_submit = True
        self.fields["document"].validators = [self.document_validator]
        
        # self.fields["created_by"].
        # self.instance.created_by = kwargs.get("instance", None)

    def document_validator(self, value):
        """Check value against the JSON schema
        TODO: Maybe implement multi validation error mapping (yeah nah).
        """
        try:
            # self._validator(value)
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

        # raise forms.ValidationError(
        #     "This is a custom validation error for the document field."
        # )
