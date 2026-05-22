import type { IApplicationData } from "../../context/types/Application";
import type { IAuthorisationProcess, IQuestionnaireData } from "../../context/types/Questionnaire";

/**
 * Create a deterministic authorisation process fixture for frontend tests.
 */
export const makeProcess = (overrides: Partial<IAuthorisationProcess> = {}): IAuthorisationProcess => ({
  slug: "s40",
  name: "Section 40",
  description: "Section 40 authorisation process",
  sort_order: 1,
  can_review: false,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
  ...overrides,
});

/**
 * Create a deterministic application fixture for list and card tests.
 */
export const makeApplication = (overrides: Partial<IApplicationData> = {}): IApplicationData => ({
  id: 1,
  key: "11111111-1111-1111-1111-111111111111",
  internal_id: "s40-new-1/26-05",
  owner: "applicant",
  process_slug: "s40",
  questionnaire_id: 1,
  questionnaire_code: "new",
  questionnaire_name: "New application",
  questionnaire_version: 1,
  status: "SUBMITTED",
  created_at: "2026-05-10T01:00:00Z",
  updated_at: "2026-05-12T01:00:00Z",
  submitted_at: "2026-05-12T02:00:00Z",
  ...overrides,
});

/**
 * Create a deterministic questionnaire fixture for new-application view tests.
 */
export const makeQuestionnaire = (
  overrides: Partial<IQuestionnaireData> = {},
): IQuestionnaireData => ({
  process_slug: "s40",
  id: 1,
  code: "new",
  name: "New application",
  version: 1,
  description: "Create a new application",
  created_at: "2026-05-01T00:00:00Z",
  document: {
    schema_version: "2025.07-1",
    steps: [
      {
        title: "Step 1",
        description: "",
        sections: [
          {
            title: "Section 1",
            description: "",
            questions: [
              {
                label: "Question 1",
                type: "text",
                is_required: false,
                description: "",
              },
            ],
          },
        ],
      },
    ],
  },
  ...overrides,
});
