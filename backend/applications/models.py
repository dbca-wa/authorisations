import io
import uuid

from django.conf import settings
from django.db import models
from django.template.loader import render_to_string
from django.utils import timezone
from django_jsonform.models.fields import JSONField
from users.models import User

from .prince import Prince
from .schema import get_answers_schema


def _boolean_checkbox(value):
    """Return a checkbox glyph for boolean answers in the PDF output."""
    return "☑ Yes" if value else "☐ No"


def _normalise_answer_value(value, question, attachments_by_key):
    """Convert stored answer values into readable plain text for PDF export."""
    question_type = (question or {}).get("type")

    # Prince renders these Unicode glyphs reliably in the current template font stack.
    if isinstance(value, bool) or question_type == "checkbox":
        return _boolean_checkbox(value)

    # Preserve a clear distinction between a blank answer and a negative boolean.
    if value is None or value == "":
        return "Not provided"

    # Grid answers are flattened into labelled multi-line rows for the simple PDF table layout.
    if question_type == "grid" and isinstance(value, list):
        rows = []
        for row_index, row in enumerate(value, start=1):
            if not isinstance(row, dict):
                rows.append(f"Row {row_index}: {row}")
                continue

            columns = []
            for column in question.get("grid_columns") or []:
                column_label = column.get("label") or "Column"
                column_value = row.get(column_label)
                if column_value is None:
                    continue
                if isinstance(column_value, bool):
                    column_value = _boolean_checkbox(column_value)
                columns.append(f"{column_label}: {column_value}")

            for column_key, column_value in row.items():
                if any(
                    (column.get("label") == column_key)
                    for column in question.get("grid_columns") or []
                ):
                    continue
                if isinstance(column_value, bool):
                    column_value = _boolean_checkbox(column_value)
                columns.append(f"{column_key}: {column_value}")

            rows.append(
                f"Row {row_index}: " + "; ".join(columns)
                if columns
                else f"Row {row_index}"
            )

        return "\n".join(rows) if rows else "Not provided"

    # File answers are stored as attachment UUIDs, so resolve them to stable human-readable names.
    if question_type == "file" and isinstance(value, list):
        attachment_names = []
        for attachment_key in value:
            attachment = attachments_by_key.get(str(attachment_key))
            attachment_names.append(
                attachment.name if attachment else str(attachment_key)
            )
        return "\n".join(attachment_names) if attachment_names else "Not provided"

    if isinstance(value, list):
        return "\n".join(str(item) for item in value) if value else "Not provided"

    if isinstance(value, dict):
        return (
            "\n".join(f"{key}: {item}" for key, item in value.items()) or "Not provided"
        )

    return str(value)


def _build_grid_rows(raw_value, question, attachments_by_key):
    """Convert a grid answer into table rows consumable by the PDF template."""
    if not isinstance(raw_value, list):
        return []

    grid_columns = question.get("grid_columns") or []
    rows = []

    for row in raw_value:
        if not isinstance(row, dict):
            continue

        cells = []
        for column in grid_columns:
            column_label = column.get("label") or "Column"
            column_type = column.get("type") or "text"

            # Use the column type so checkbox/date cells are normalised predictably.
            cell_value = _normalise_answer_value(
                row.get(column_label),
                {"type": column_type},
                attachments_by_key,
            )
            cells.append(cell_value)

        rows.append(cells)

    return rows


def _build_question_item(question, answer_value, question_index, attachments_by_key):
    """Build a template-friendly question payload for PDF rendering."""
    question_type = question.get("type") or "text"
    question_label = question.get("label") or f"Question {question_index + 1}"

    item = {
        "label": question_label,
        "type": question_type,
    }

    if question_type == "grid":
        item["grid_columns"] = [
            column.get("label") or "Column"
            for column in question.get("grid_columns") or []
        ]
        item["grid_rows"] = _build_grid_rows(
            answer_value,
            question,
            attachments_by_key,
        )
        return item

    if question_type == "file" and isinstance(answer_value, list):
        files = []
        for attachment_key in answer_value:
            attachment = attachments_by_key.get(str(attachment_key))
            files.append(attachment.name if attachment else str(attachment_key))

        item["files"] = files
        return item

    item["value"] = _normalise_answer_value(
        answer_value,
        question,
        attachments_by_key,
    )
    return item


class ApplicationStatus(models.TextChoices):
    """Enumeration of possible application statuses."""

    DRAFT = "DRAFT"
    DISCARDED = "DISCARDED"
    SUBMITTED = "SUBMITTED"
    # WITHDRAWN = "WITHDRAWN"
    UNDER_REVIEW = "UNDER_REVIEW"
    ACTION_REQUIRED = "ACTION_REQUIRED"
    PROCESSING = "PROCESSING"
    # UNDER_ASSESSMENT = "UNDER_ASSESSMENT"
    APPROVED = "APPROVED"
    # APPROVED_WITH_CONDITIONS = "APPROVED_WITH_CONDITIONS"
    # DEFERRED = "DEFERRED"
    REJECTED = "REJECTED"


class Application(models.Model):
    """Model to represent an application."""

    id = models.BigAutoField(primary_key=True)
    key = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    owner = models.ForeignKey(
        "users.User",
        on_delete=models.PROTECT,
        related_name="applications",
        db_index=False,
        editable=False,
    )
    questionnaire = models.ForeignKey(
        "questionnaires.Questionnaire",
        on_delete=models.PROTECT,
        related_name="applications",
        db_index=False,
        editable=False,
    )
    status = models.CharField(
        max_length=20,
        choices=ApplicationStatus.choices,
        default=ApplicationStatus.DRAFT,
        editable=False,
    )
    document = JSONField(
        schema=get_answers_schema(),
        blank=False,
        null=False,
        editable=True,
    )
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)
    submitted_at = models.DateTimeField(blank=True, null=True, editable=False)

    # Create multiple column indexes for:
    # - user, status, created_at DESC
    # - questionnaire, status, created_at DESC
    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["owner", "status", "-created_at"],
                name="apps_owner_status_idx",
            ),
            models.Index(
                fields=["questionnaire", "status", "-created_at"],
                name="apps_questionnaire_status_idx",
            ),
        ]

    def __str__(self):
        return f"Application #{self.id} by {self.owner.username} for {self.questionnaire.name}"

    @property
    def internal_id(self) -> str:
        """Generate a unique human-readable identifier combining process slug, questionnaire code and application id."""
        submitted_at_suffix = self.submitted_at.strftime("/%y-%m") if self.submitted_at else ""
        return f"{self.questionnaire.process.slug}-{self.questionnaire.code}-{self.id}{submitted_at_suffix}"

    def has_access(self, user: User) -> bool:
        """
        Returns True if the user has access to this application.
        - Owners always have access.
        - TODO: Extend this logic for Technical Officers or other roles in the future.
        """
        if not user.is_authenticated:
            return False

        if self.owner == user:
            return True

        # TODO: Add logic for Technical Officers or other roles
        return False

    def build_pdf_context(self):
        """Build nested step/section/question data used by the PDF review template."""
        questionnaire_document = self.questionnaire.document or {}
        application_document = self.document or {}
        questionnaire_steps = questionnaire_document.get("steps") or []
        application_steps = application_document.get("steps") or []

        # Resolve file upload answers once so repeated lookups stay deterministic.
        attachments_by_key = {
            str(attachment.key): attachment
            for attachment in self.attachments.filter(is_deleted=False)
        }

        steps = []
        for step_index, step in enumerate(questionnaire_steps):
            step_state = (
                application_steps[step_index]
                if step_index < len(application_steps)
                else {}
            )
            answers = step_state.get("answers") or {}
            step_payload = {
                "title": step.get("title") or f"Step {step_index + 1}",
                "sections": [],
            }

            for section_index, section in enumerate(step.get("sections") or []):
                section_payload = {
                    "prefix": f"{chr(65 + section_index)})",
                    "title": section.get("title") or f"Section {section_index + 1}",
                    "description": section.get("description") or "",
                    "questions": [],
                }

                for question_index, question in enumerate(
                    section.get("questions") or []
                ):
                    answer_key = f"{section_index}-{question_index}"
                    answer_value = answers.get(answer_key)
                    section_payload["questions"].append(
                        _build_question_item(
                            question,
                            answer_value,
                            question_index,
                            attachments_by_key,
                        )
                    )

                step_payload["sections"].append(section_payload)

            steps.append(step_payload)

        return {
            "application": self,
            "steps": steps,
        }

    def render_pdf_html(self):
        """Render the standalone HTML template used as the Prince input document."""
        return render_to_string(
            "application-pdf-template.html",
            self.build_pdf_context(),
        )

    def generate_pdf(self, request=None):
        """Render the application HTML and convert it to a PDF using Prince XML."""
        prince_bin = getattr(settings, "PRINCE_BIN", "prince")
        html = self.render_pdf_html()

        # Write the HTML to a temporary file for debugging purposes (optional)
        # with open(
        #     f"/tmp/application_{self.id}.html", "w", encoding="utf-8"
        # ) as temp_html_file:
        #     temp_html_file.write(html)

        # Prefer the current request origin so Prince resolves root-relative static URLs
        # against the actual running Django host instead of a hardcoded dev address.
        base_url = request.build_absolute_uri("/") if request is not None else None

        # Prince returns raw PDF bytes when output is directed to stdout.
        pdf_bytes = Prince(prince_bin=prince_bin).from_string(
            html,
            # Base URL is required to resolve static assets like images and CSS.
            options={"--baseurl": base_url} if base_url else {},
        )
        pdf_buffer = io.BytesIO(pdf_bytes)
        pdf_buffer.seek(0)
        return pdf_buffer


# def certificate_path(instance, filename):
#     """Define the upload path for the certificate file."""
#     return f"certificates/{instance.application.id}/{filename}"


# class ApplicationCertificate(models.Model):
#     """Model to represent a certificate issued for an application."""

#     application = models.OneToOneField(
#         Application,
#         primary_key=True,
#         on_delete=models.CASCADE,
#         related_name="certificate",
#     )
#     certificate = models.FileField(upload_to=certificate_path, blank=False, null=False)
#     issued_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"Certificate for the application #{self.application.id} issued at {self.issued_at}"


def attachment_upload_path(instance, filename):
    """Define the upload path for the attachment file."""
    created_month = instance.application.created_at.strftime("%Y-%m")
    return f"attachments/{created_month}/{instance.application.key}/{instance.key}"


class ApplicationAttachment(models.Model):
    """Model to represent a file attached to an application."""

    id = models.BigAutoField(primary_key=True)
    key = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name="attachments",
        db_index=True,
        editable=False,
    )
    question = models.CharField(max_length=100, blank=False, null=False)
    name = models.CharField(max_length=255, blank=False, null=False)
    file = models.FileField(
        upload_to=attachment_upload_path,
        blank=False,
        null=False,
    )
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    deleted_at = models.DateTimeField(blank=True, null=True, editable=False)

    class Meta:
        indexes = [
            models.Index(
                fields=["application", "is_deleted"],
                name="attachments_app_deleted_idx",
            ),
        ]

    def __str__(self):
        return f"Attachment {self.key} for Application {self.application.id}"

    def soft_delete(self):
        """
        Mark the attachment as deleted and record when.
        """
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at"])

    def get_download_url(self, request):
        """Generate a download URL for this attachment."""
        return request.build_absolute_uri(f"/d/{self.application.key}/{self.key}")
