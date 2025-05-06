/**
 * ApplicationForm interface represents the structure of an application form.
 */
type PrimitiveType = string | number | boolean | null;

export interface ApplicationForm {
    name: string;
    steps: FormStep[];
}

export interface FormStep {
    title: string;
    shortDescription: string;
    sections: FormSection[];
}

export interface FormSection {
    title: string;
    description?: string;
    questions: RootQuestion[];
}

// Root-level questions can include GridQuestion
export type RootQuestion = Question | GridQuestion;

// Nested questions cannot include GridQuestion
export interface Question {
    label: string;
    type: string;
    isRequired?: boolean;
    value?: PrimitiveType; // OR date?
    options?: string[]; // For multiselect types
    description?: string;
}

export interface GridQuestion extends Omit<Question, "value"> {
    type: "grid";
    maxRows: number;
    // Only basic Question types allowed here
    columns: Question[]; 
    values: PrimitiveType[][]; // 2D array for grid values
}