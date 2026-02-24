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

export interface IQuestion {
    label: string;
    type: string;
    is_required: boolean;
    description?: string;
    // For select types
    select_options?: string[] | null;
    // Grid columns definitions
    grid_columns?: IGridQuestionColumn[] | null;
    // Indicates the maximum number of rows for grid types
    grid_max_rows?: number | null;
    dependent_step?: number | null;
}


export interface IGridQuestionColumn {
    label: string;
    type: string;
    description?: string;
    select_options?: string[]; // For select types
}


/**
 * Step, section and question indices (used for form validation and display)
 */
export interface IQuestionIndices {
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

    get key(): string {
        return `${this.indices.step}.${this.indices.section}-${this.indices.question}`;
    }

    // Return formmatted label for display
    get labelText(): string {
        const formatted = `${this.indices.question + 1}. ${this.o.label}`;
        // Append asterisk for required fields
        return this.o.is_required ? `${formatted} *` : formatted;
    }
}


