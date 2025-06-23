import AppBar from "@mui/material/AppBar";
import Box from "@mui/material/Box";
import Toolbar from "@mui/material/Toolbar";
import Typography from "@mui/material/Typography";
import React from "react";

import { FormStepContext } from "../../context/FormContext";
// import type { ApplicationForm } from "../../context/FormTypes";
// import untypedFormData from '../../data/formData.json';
import { Sidebar } from "./Sidebar";
import { ActiveStepForm } from "./ActiveStepForm";
import { useLoaderData } from "react-router";
// const formData: ApplicationForm = untypedFormData;


export function MainLayout() {
    // Manage activeStep state here
    const [activeStep, setActiveStep] = React.useState(0);
    
    const questionnaire = useLoaderData();
    console.log("Data:", typeof(questionnaire), questionnaire);

    // Set the FormStepContext value
    const contextValue = {
        setActiveStep,
        currentStep: questionnaire.document.steps[activeStep],
        isFirst: activeStep === 0,
        isLast: activeStep === questionnaire.document.steps.length - 1,
    };

    return (
        <Box sx={{ display: 'flex' }}>
            <AppBar position="fixed">
                <Toolbar>
                    <Typography variant="h6" noWrap component="div">
                        {questionnaire.name}
                    </Typography>
                </Toolbar>
            </AppBar>

            <Sidebar steps={questionnaire.document.steps} activeStep={activeStep} />
            
            <Box
                component="main"
                sx={{ p: 1 }}
            >
                <Toolbar />
                <FormStepContext.Provider value={contextValue}>
                    <ActiveStepForm />
                </FormStepContext.Provider>
            </Box>
        </Box>
    );
}
