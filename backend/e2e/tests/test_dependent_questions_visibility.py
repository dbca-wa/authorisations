"""E2E tests for dependent-question visibility on the review page."""

import pytest
from applications.models import Application
from applications.schema import SCHEMA_VERSION
from processes.models import AuthorisationProcess
from questionnaires.models import Questionnaire


def _create_application_with_questionnaire(
    *,
    owner,
    questionnaire_document: dict,
    answers: dict[str, object],
) -> Application:
    """Create a draft application with a custom questionnaire document and answers."""
    process = AuthorisationProcess.objects.create(
        slug=f"dependent-visibility-{owner.id}-{AuthorisationProcess.objects.count()}",
        name="Dependent visibility process",
        description="E2E process for dependent visibility",
        sort_order=99,
    )
    questionnaire = Questionnaire.objects.create(
        process=process,
        code="dependent-visibility",
        name="Dependent visibility questionnaire",
        description="E2E questionnaire for dependent visibility",
        sort_order=1,
        created_by=owner,
        updated_by=owner,
        document=questionnaire_document,
    )

    return Application.objects.create(
        owner=owner,
        questionnaire=questionnaire,
        document={
            "schema_version": SCHEMA_VERSION,
            "active_step": 0,
            "steps": [
                {
                    "is_valid": True,
                    "answers": answers,
                }
            ],
        },
    )


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
def test_review_hides_dependent_question_when_parent_is_no_case_insensitive(
    authenticated_browser_context_factory,
    e2e_users,
    mock_turnstile_script,
):
    """Hide a dependent question on review when parent answer is 'NO'."""
    applicant = e2e_users["applicant"]
    application = _create_application_with_questionnaire(
        owner=applicant,
        questionnaire_document={
            "schema_version": SCHEMA_VERSION,
            "steps": [
                {
                    "title": "Step 1",
                    "description": "",
                    "sections": [
                        {
                            "title": "Section 1",
                            "description": "",
                            "questions": [
                                {
                                    "label": "Do you have approval?",
                                    "type": "select",
                                    "is_required": True,
                                    "config": {"select_options": ["No", "Yes"]},
                                },
                                {
                                    "label": "Approval details",
                                    "type": "text",
                                    "is_required": True,
                                    "config": {"dependent_step": 1},
                                },
                            ],
                        }
                    ],
                }
            ],
        },
        answers={"0-0": "NO", "0-1": ""},
    )

    context = authenticated_browser_context_factory(applicant)
    page = context.new_page()
    mock_turnstile_script(page)

    try:
        page.goto(f"/a/{application.key}")
        page.wait_for_load_state("networkidle", timeout=5000)
        page.get_by_role("button", name="Continue").click()
        page.get_by_text("Review your answers", exact=True).wait_for(timeout=5000)

        assert page.get_by_text("1. Do you have approval? *", exact=True).is_visible()
        assert page.get_by_text("NO", exact=True).is_visible()
        assert page.get_by_text("2. Approval details *", exact=True).count() == 0
        assert page.get_by_text("(Not provided)", exact=True).count() == 0
    finally:
        page.close()
        context.close()


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
def test_review_shows_dependent_question_when_parent_is_truthy(
    authenticated_browser_context_factory,
    e2e_users,
    mock_turnstile_script,
):
    """Show a dependent question on review when parent answer is truthy."""
    applicant = e2e_users["applicant"]
    application = _create_application_with_questionnaire(
        owner=applicant,
        questionnaire_document={
            "schema_version": SCHEMA_VERSION,
            "steps": [
                {
                    "title": "Step 1",
                    "description": "",
                    "sections": [
                        {
                            "title": "Section 1",
                            "description": "",
                            "questions": [
                                {
                                    "label": "Do you have approval?",
                                    "type": "select",
                                    "is_required": True,
                                    "config": {"select_options": ["No", "Yes"]},
                                },
                                {
                                    "label": "Approval details",
                                    "type": "text",
                                    "is_required": True,
                                    "config": {"dependent_step": 1},
                                },
                            ],
                        }
                    ],
                }
            ],
        },
        answers={"0-0": "Yes", "0-1": "Permit 123"},
    )

    context = authenticated_browser_context_factory(applicant)
    page = context.new_page()
    mock_turnstile_script(page)

    try:
        page.goto(f"/a/{application.key}")
        page.wait_for_load_state("networkidle", timeout=5000)
        page.get_by_role("button", name="Continue").click()
        page.get_by_text("Review your answers", exact=True).wait_for(timeout=5000)

        assert page.get_by_text("2. Approval details *", exact=True).is_visible()
        assert page.get_by_text("Permit 123", exact=True).is_visible()
    finally:
        page.close()
        context.close()


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
def test_review_keeps_dependent_scope_within_same_section(
    authenticated_browser_context_factory,
    e2e_users,
    mock_turnstile_script,
):
    """Treat out-of-bounds walkback as independent instead of crossing sections."""
    applicant = e2e_users["applicant"]
    application = _create_application_with_questionnaire(
        owner=applicant,
        questionnaire_document={
            "schema_version": SCHEMA_VERSION,
            "steps": [
                {
                    "title": "Step 1",
                    "description": "",
                    "sections": [
                        {
                            "title": "Section A",
                            "description": "",
                            "questions": [
                                {
                                    "label": "Section A parent answer",
                                    "type": "select",
                                    "is_required": False,
                                    "config": {"select_options": ["No", "Yes"]},
                                }
                            ],
                        },
                        {
                            "title": "Section B",
                            "description": "",
                            "questions": [
                                {
                                    "label": "Section B standalone question",
                                    "type": "text",
                                    "is_required": False,
                                    "config": {"dependent_step": 1},
                                }
                            ],
                        },
                    ],
                }
            ],
        },
        answers={"0-0": "NO", "1-0": "Visible in section B"},
    )

    context = authenticated_browser_context_factory(applicant)
    page = context.new_page()
    mock_turnstile_script(page)

    try:
        page.goto(f"/a/{application.key}")
        page.wait_for_load_state("networkidle", timeout=5000)
        page.get_by_role("button", name="Continue").click()
        page.get_by_text("Review your answers", exact=True).wait_for(timeout=5000)

        assert page.get_by_text("1. Section B standalone question", exact=True).is_visible()
        assert page.get_by_text("Visible in section B", exact=True).is_visible()
    finally:
        page.close()
        context.close()
