"use client";
import Box from '@mui/material/Box';
import ApplicationSteps, { StepsContext } from '../common/steps';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import Drawer from '@mui/material/Drawer';
import makeStyles from '@mui/styles/makeStyles';
import React from 'react';

const steps = [
    {
        label: 'Terms of Service',
        description: 'Read and accept the terms of service.',
    },
    {
        label: 'Scientific Review',
        description: 'Submit your project for scientific review.',
    },
    {
        label: 'Competencies & Declarations',
        description: 'Provide your competencies and declarations.',
    },
    {
        label: 'Project Details',
        description: 'Fill in the details of your project.',
    },
    {
        label: 'Replacement',
        description: 'Describe the alternatives to animal use in your project.',
    },
    {
        label: 'Reduction',
        description: 'Explain how you will reduce the number of animals used.',
    },
    {
        label: 'Refinement',
        description: 'Outline how you will refine your methods to minimize suffering.',
    },
    {
        label: 'Adverse Effects',
        description: 'Describe any potential adverse effects on animals.',
    },
    {
        label: 'References & Sources',
        description: 'References/sources used to prepare this application.',
    },
    {
        label: 'Review & Submit',
        description: 'Review your application and submit it.',
    },
];

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
    const [activeStep, setActiveStep] = React.useState(0); // Manage activeStep state here

    const classes = useStyles();

    return (
        <Box sx={{ display: 'flex' }}>
            <AppBar position="fixed">
                <Toolbar>
                    <Typography variant="h6" noWrap component="div">
                        Animal Ethics Committee
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
                {/* Provide both activeStep and setActiveStep via context */}
                <StepsContext.Provider value={{ activeStep, setActiveStep }}>
                    <ApplicationSteps 
                        steps={steps}
                        activeStep={activeStep} // Pass activeStep to ApplicationSteps
                    />
                </StepsContext.Provider>
            </Drawer>
            <Box
                component="main"
                sx={{ flexGrow: 1, p: 1 }}
            >
                <Toolbar />
                {/* Provide both activeStep and setActiveStep via context */}
                <StepsContext.Provider value={{ activeStep, setActiveStep }}>
                    {children}
                </StepsContext.Provider>
            </Box>
        </Box>
    );
}