/**
 * ApplicationForm interface represents the structure of an application form.
 */
type PrimitiveType = string | number | boolean | null;

export default interface ApplicationForm {
    name: string;
    sections: Section[];
}

export interface Section {
    title: string;
    shortDescription: string;
    longDescription: string;
    questions: RootQuestion[];
}

// Root-level questions can include GridQuestion
export type RootQuestion = Question | GridQuestion;

// Nested questions cannot include GridQuestion
export interface Question {
    label: string;
    type: string;
    isRequired: boolean;
    value?: PrimitiveType; // OR date?
    description?: string;
}

export interface GridQuestion extends Omit<Question, "type" | "value"> {
    type: "grid";
    maxRows: number;
    // Only basic Question types allowed here
    columns: Question[]; 
    values: PrimitiveType[][]; // 2D array for grid values
}