/**
 * ApplicationForm interface represents the structure of an application form.
 */

export default interface ApplicationForm {
    name: string;
    sections: Section[];
}

export interface Section {
    title: string;
    shortDescription: string;
    longDescription: string;
    questions: Question[];
}

export interface Question {
    label: string;
    type: string;
    isRequired: boolean;
    description?: string;
}
