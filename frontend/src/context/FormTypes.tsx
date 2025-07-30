export type PrimitiveType = string | number | boolean | null;

/** 
 * Interface for a questionnaire data including meta data 
 */
export interface IQuestionnaireData {
    slug: string;
    version: number;
    name: string;
    description: string;
    created_at: string;
    document: IQuestionnaire;
}

/**
 * Interface for a questionnaire document in JSON Schema structure
 */
export interface IQuestionnaire {
    schema_version: string;
    steps: IFormStep[];
}

export interface IFormStep {
    title: string;
    description: string;
    sections: IFormSection[];
}

export interface IFormSection {
    title: string;
    description?: string;
    questions: IQuestion[];
}

export interface IGridQuestionColumn {
    label: string;
    type: string;
    description?: string;
    select_options?: string[]; // For select types
}

export interface IQuestion {
    label: string;
    type: string;
    is_required: boolean;
    description?: string;
    select_options?: string[] | null; // For select types
    grid_max_rows?: number | null; // For grid types, indicates the maximum number of rows
    grid_columns?: IGridQuestionColumn[] | null;
}

/**
 * Step, section and question indices (used for form validation and display)
 */
interface IQuestionIndices {
    step: number;
    section: number;
    question: number;
}

/**
 * Class representing a question with its indices in the questionnaire form
 */
export class Question {
    public readonly o: IQuestion;
    public readonly indices: IQuestionIndices;

    constructor(obj: IQuestion, indices: IQuestionIndices) {
        this.o = obj;
        this.indices = indices;
    }

    get id(): string {
        return `${this.indices.step}-${this.indices.section}-${this.indices.question}`;
    }

    // Return formmatted label for display
    get labelText(): string {
        const formatted = `${this.indices.question + 1}. ${this.o.label}`;
        // Append asterisk for required fields
        return this.o.is_required ? `${formatted} *` : formatted;
    }
}

/**
 * Interface for application data, which includes the answers and meta data
 */
export interface IApplicationData {
    key: string;
    questionnaire_slug: string;
    questionnaire_version: number;
    questionnaire_name: string;
    status: string;
    created_at: string;
    updated_at: string;
    submitted_at: string | null;
    answers: IAnswers;
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
