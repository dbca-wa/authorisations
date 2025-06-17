/**
 * ApplicationForm interface represents the structure of an application form.
 */
export type PrimitiveType = string | number | boolean | null;

export interface ApplicationForm {
    schema_version: string;
    // name: string;
    steps: FormStep[];
}

export interface FormStep {
    title: string;
    description: string;
    sections: FormSection[];
}

export interface FormSection {
    title: string;
    description?: string;
    questions: Question[];
}

export interface Question {
    label: string;
    type: string;
    is_required: boolean;
    description?: string;
    select_options?: string[] | null; // For select types
    grid_max_rows?: number | null; // For grid types, indicates the maximum number of rows
    grid_columns?: GridQuestionColumn[] | null; 
    // Remove value & values from Question
    value?: PrimitiveType; // date as string?
    values?: PrimitiveType[][]; // 2D array for grid values
}

interface GridQuestionColumn {
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