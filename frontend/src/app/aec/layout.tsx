"use client";
import AppBar from '@mui/material/AppBar';
import Box from '@mui/material/Box';
import Drawer from '@mui/material/Drawer';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import makeStyles from '@mui/styles/makeStyles';
import React from 'react';
import { FormStepContext } from '../context/FormContext';
import { ApplicationForm } from '../data/FormData';
import { ApplicationSteps } from './steps';

const formData: ApplicationForm = require('@/app/data/formData.json');
const drawerWidth = 320;
const useStyles = makeStyles({
    drawerPaper: {
        backgroundColor: "transparent",
        marginTop: "84px",
        paddingBottom: "84px",
        paddingLeft: "30px",
    }
});

export default function FormLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    // Manage activeStep state here
    const [activeStep, setActiveStep] = React.useState(0);
    const classes = useStyles();

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

            <Drawer
                classes={{ paper: classes.drawerPaper }}
                sx={{
                    width: drawerWidth,
                    flexShrink: 0,
                    '& .MuiDrawer-paper': {
                        width: drawerWidth,
                        boxSizing: 'border-box',
                    },
                }}
                variant="permanent"
                anchor="left"
            >
                <ApplicationSteps
                    steps={formData.steps}
                    activeStep={activeStep}
                />
            </Drawer>
            <Box
                component="main"
                sx={{ flexGrow: 1, p: 1 }}
            >
                <Toolbar />
                <FormStepContext.Provider value={contextValue}>
                    {children}
                </FormStepContext.Provider>
            </Box>
        </Box>
    );
}