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
    // questionnaire_id: number;
    questionnaire_slug: string;
    questionnaire_name: string;
    questionnaire_version: number;
    status: ApplicationStatus;
    created_at: string;
    updated_at: string;
    submitted_at: string | null;
    document: {
        answers: IAnswers;
        schema_version: string;
    };
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
 * Interface for an application answer document in JSON Schema structure
 */
export interface IAnswers {
    [key: string]: IAnswer;
}
