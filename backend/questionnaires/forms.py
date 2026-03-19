import re

from django import forms
from django_jsonform.utils import join_coords
from django_jsonform.validators import JSONSchemaValidationError
from jsonschema import ValidationError, validate

from .models import Questionnaire
from .schema import get_questionnaire_schema


class QuestionnaireForm(forms.ModelForm):
    """Admin form for the Questionnaire model.

    Wires a JSON Schema validator onto the ``document`` field and enforces a
    case-insensitive uniqueness check on (process, name) at the form level so
    that a move or rename cannot silently collide with an existing questionnaire
    lineage in the target process.
    """

    _schema = get_questionnaire_schema()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Attach the JSON Schema validator to the document field.
        # Turn this back on when the nullable integer issue is fixed
        # https://github.com/bhch/django-jsonform/issues/192
        # self.fields["document"].widget.validate_on_submit = True
        self.fields["document"].validators = [self.document_validator]

    def document_validator(self, value):
        """Validate the ``document`` field against the questionnaire JSON Schema.

        Called automatically by Django's field validation before ``clean()``.
        Raises ``JSONSchemaValidationError`` with a coordinate hint if the
        submitted value does not conform to the schema.  An unchanged document
        is intentionally allowed here because metadata-only edits (process,
        name, description) do not require a content change.

        Args:
            value: The submitted document value (a plain Python dict).

        Raises:
            JSONSchemaValidationError: When the value violates the JSON Schema.
        """
        try:
            validate(value, self._schema)
        except ValidationError as exc:
            # Map the JSON Schema error path back to a widget coordinate so
            # django-jsonform can highlight the offending field inline.
            coordinate = join_coords(*list(exc.absolute_path))
            raise JSONSchemaValidationError(
                message=f"Validation error: {exc.message} ({coordinate})",
                error_map={coordinate: exc.message},
            )

    def clean_name(self):
        """Normalise whitespace and validate allowed questionnaire name characters.

        Allowed characters are letters, digits, spaces, and the ordinary
        hyphen (``-``). Disallowed characters are rejected with a validation
        error rather than silently modified.
        """
        name = self.cleaned_data["name"]
        # Safe normalisation: trim ends and collapse repeated inner whitespace.
        name = " ".join(name.split())

        if name.startswith("-") or name.endswith("-"):
            raise forms.ValidationError(
                "Questionnaire name cannot start or end with a hyphen (-)."
            )

        if re.search(r"[^A-Za-z0-9\- ]", name):
            raise forms.ValidationError(
                "Use only letters, numbers, spaces, and hyphen (-)."
            )

        return name
    
    def clean(self):
        """Cross-field validation: enforce case-insensitive (process, name) uniqueness.

        Runs after all individual field validators have passed.  Guards against
        a rename or move that would collide with an existing questionnaire
        lineage in the target process.

        When ``process`` or ``name`` is absent from ``cleaned_data`` it means a
        prior field-level error already made one of them invalid (e.g. the field
        was left blank, the selected process pk no longer exists, or a
        read-only field was missing from the POST payload).  Django excludes
        such fields from ``cleaned_data``, so ``.get()`` returns ``None``.
        There is no point running the cross-field uniqueness check against
        partial data, so we return early and let the existing field error
        surface to the user instead.

        Returns:
            dict: The validated cleaned data, unchanged except for the possible
            addition of a ``name`` field error.
        """
        cleaned_data = super().clean()

        process = cleaned_data.get("process")
        name = cleaned_data.get("name")

        # Abort cross-field check if either anchor field failed its own validation.
        if not process or not name:
            return cleaned_data

        # Find any questionnaire in the target process with the same name,
        # using a case-insensitive match to prevent near-duplicate lineages.
        conflicts = Questionnaire.objects.filter(process=process, name__iexact=name)

        if self.instance and self.instance.pk:
            # Exclude the current questionnaire's own lineage (matched by the
            # original process + name before edits) so a no-op save or a pure
            # description edit does not trigger a false conflict.
            conflicts = conflicts.exclude(
                process_id=self.instance.process_id,
                name=self.instance.name,
            )

        if conflicts.exists():
            self.add_error(
                "name",
                forms.ValidationError(
                    "A questionnaire with this name already exists for the selected process (case-insensitive)."
                ),
            )

        return cleaned_data
