import AppBar from "@mui/material/AppBar";
import Box from "@mui/material/Box";
import Toolbar from "@mui/material/Toolbar";
import Typography from "@mui/material/Typography";
import React from "react";

import { FormStepContext } from "../../context/FormContext";
import type { ApplicationForm } from "../../context/FormTypes";
import untypedFormData from '../../data/formData.json';
import { Sidebar } from "./Sidebar";
import { ActiveStepForm } from "./ActiveStepForm";
const formData: ApplicationForm = untypedFormData;


export function MainLayout() {
    // Manage activeStep state here
    const [activeStep, setActiveStep] = React.useState(0);

    // Set the FormStepContext value
    const contextValue = {
        setActiveStep,
        currentStep: formData.steps[activeStep],
        isFirst: activeStep === 0,
        isLast: activeStep === formData.steps.length - 1,
    };

    return (
        <Box sx={{ display: 'flex' }}>
            <AppBar position="fixed">
                <Toolbar>
                    <Typography variant="h6" noWrap component="div">
                        {formData.name}
                    </Typography>
                </Toolbar>
            </AppBar>

            <Sidebar steps={formData.steps} activeStep={activeStep} />
            
            <Box
                component="main"
                sx={{ flexGrow: 1, p: 1 }}
            >
                <Toolbar />
                <FormStepContext.Provider value={contextValue}>
                    <ActiveStepForm />
                </FormStepContext.Provider>
            </Box>
        </Box>
    );
}
