"""Application status enumerations and status categories.

Extracted to a separate module to avoid circular imports between applications
and audit modules, both of which need to reference these statuses.
"""

from django.db import models


class ApplicationStatus(models.TextChoices):
    """Enumeration of possible application statuses.
    
    Represents all valid states an application can be in throughout its lifecycle
    from initial draft through final decision. Used by both Application model and
    audit logging to maintain consistency.
    """

    DRAFT = "DRAFT"
    DISCARDED = "DISCARDED"
    SUBMITTED = "SUBMITTED"
    WITHDRAWN = "WITHDRAWN"
    UNDER_REVIEW = "UNDER_REVIEW"
    UNDER_ASSESSMENT = "UNDER_ASSESSMENT"
    APPROVED = "APPROVED"
    APPROVED_WITH_CONDITIONS = "APPROVED_WITH_CONDITIONS"
    DEFERRED = "DEFERRED"
    REJECTED = "REJECTED"


# Statuses visible in the reviewer queue — applications awaiting or under active review.
REVIEW_QUEUE_STATUSES = frozenset(
    [
        ApplicationStatus.SUBMITTED,
        ApplicationStatus.UNDER_REVIEW,
        ApplicationStatus.UNDER_ASSESSMENT,
    ]
)

# Statuses a reviewer is permitted to set; excludes applicant-only transitions (DRAFT, DISCARDED).
REVIEWER_SETTABLE_STATUSES = frozenset(
    [
        ApplicationStatus.DRAFT,
        ApplicationStatus.UNDER_REVIEW,
        ApplicationStatus.UNDER_ASSESSMENT,
        ApplicationStatus.APPROVED,
        ApplicationStatus.APPROVED_WITH_CONDITIONS,
        ApplicationStatus.DEFERRED,
        ApplicationStatus.REJECTED,
    ]
)
