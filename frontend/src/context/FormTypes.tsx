export type PrimitiveType = string | number | boolean | null;

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

// Step, section and question indices (used for form validation and display)
interface IQuestionIndices {
    step: number;
    section: number;
    question: number;
}

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
        const formatted = `${this.indices!.question + 1}. ${this.o.label}`;
        // Append asterisk for required fields
        return this.o.is_required ? `${formatted} *` : formatted;
    }
}


export interface IGridAnswerRow {
    // Keyed by column label
    [key: string]: PrimitiveType;
}

export type IAnswer = PrimitiveType | IGridAnswerRow[];

export interface IAnswers {
    [key: string]: IAnswer;
}
