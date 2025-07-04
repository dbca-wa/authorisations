export type PrimitiveType = string | number | boolean | null;

// export interface IApplicationForm {
//     schema_version: string;
//     // name: string;
//     steps: FormStep[];
// }

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

interface IQuestion {
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

    // Remove value & values from Question
    value?: PrimitiveType; // date as string?
    values?: PrimitiveType[][]; // 2D array for grid values
}

interface IGridQuestionColumn {
    label: string;
    type: string;
    description?: string;
    select_options?: string[]; // For select types
}

// // Root-level questions can include GridQuestion
// export type RootQuestion = Question | GridQuestion;

// // Nested questions cannot include GridQuestion
// export interface Question {
//     label: string;
//     type: string;
//     is_required?: boolean;
//     value?: PrimitiveType; // date as string?
//     options?: string[]; // For select types
//     description?: string;
// }

// export interface GridQuestion extends Omit<Question, "value"> {
//     type: "grid";
//     max_rows: number;
//     // Only basic Question types allowed here
//     columns: Question[]; 
//     values: PrimitiveType[][]; // 2D array for grid values
// }