import type { IFormStep } from "./FormTypes";
import React from "react";


interface FormStepContextValue {
    setActiveStep: React.Dispatch<React.SetStateAction<number>>; // Allow functional updates
    currentStep: IFormStep; // Current step data
    stepIndex: number; // Index of the current step
    isFirst: boolean;
    isLast: boolean;
}

export const FormStepContext = React.createContext<FormStepContextValue>({
    // Default is a no-op function,
    setActiveStep: () => { },

    // Default empty step data
    currentStep: {
        title: "",
        description: '',
        sections: [],
    },
    stepIndex: 0,

    isFirst: false,
    isLast: false,
});
