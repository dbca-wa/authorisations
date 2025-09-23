import type { PrimitiveType } from "./Generic";

/**
 * Application status enum
 */
export type ApplicationStatus =
    | "DRAFT"
    | "DISCARDED"
    | "SUBMITTED"
    | "UNDER_REVIEW"
    | "ACTION_REQUIRED"
    | "PROCESSING"
    | "APPROVED"
    | "REJECTED";


export const finalisedStatuses: ApplicationStatus[] = [
    "DISCARDED",
    "APPROVED",
    "REJECTED",
]

/**
 * Interface for application data, which includes the answers and meta data
 */
export interface IApplicationData {
    key: string;
    owner: string;
    questionnaire_slug: string;
    questionnaire_name: string;
    questionnaire_version: number;
    status: ApplicationStatus;
    created_at: string;
    updated_at: string;
    submitted_at: string | null;
    document: IFormDocument;
}

/**
 * Interface corresponding to a grid answer row, where each column is keyed by its label
 */
export interface IGridAnswerRow {
    // Keyed by column label
    [key: string]: PrimitiveType;
}

/**
 * Interface for an answer, which can be either a primitive type or an array of grid answer rows
 */
export type IAnswer = PrimitiveType | IGridAnswerRow[];

/**
 * The form state for each step, keyed by step index.
 * `document.steps` is converted into this structure for easer access.
 */
export interface IFormAnswers {
    [stepIndex: number]: {
        [qKey: string]: IAnswer;
    };
}

/**
 * Interface for the state of each step in the application form
 */
export interface IStepState {
    is_valid: boolean | null;
    answers: {
        [qKey: string]: IAnswer;
    };
}

/**
 * Interface for an application form document in JSON Schema structure.
 * This is essentially the current state of the form.
 */
export interface IFormDocument {
    schema_version: string;
    active_step: number;
    steps: IStepState[];
}