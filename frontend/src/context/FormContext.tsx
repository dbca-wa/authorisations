import type { FormStep } from "./FormTypes";
import React from "react";


interface FormStepContextValue {
    setActiveStep: React.Dispatch<React.SetStateAction<number>>; // Allow functional updates
    currentStep: FormStep; // Current step data
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

    isFirst: false,
    isLast: false,
});
