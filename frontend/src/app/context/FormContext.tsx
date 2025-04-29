"use client";
import React from "react";
import ApplicationForm from "../data/FormData";

interface ApplicationFormContextValue {
    activeSection: number;
    setActiveSection: React.Dispatch<React.SetStateAction<number>>; // Allow functional updates
    formData: ApplicationForm;
}


const ApplicationFormContext = React.createContext<ApplicationFormContextValue>({
    activeSection: 0,
    
    // Default is a no-op function,
    setActiveSection: () => { }, 
    
    // Default empty form data
    formData: {
        name: "",
        sections: [],
    }, 
});

export default ApplicationFormContext;