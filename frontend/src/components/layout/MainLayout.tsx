import MenuIcon from '@mui/icons-material/Menu';
import MuiAppBar, { type AppBarProps as MuiAppBarProps } from '@mui/material/AppBar';
import Box from "@mui/material/Box";
import IconButton from "@mui/material/IconButton";
import Toolbar from "@mui/material/Toolbar";
import Typography from "@mui/material/Typography";
import React from "react";

import { styled } from '@mui/material/styles';
import { FormProvider, useForm } from 'react-hook-form';
import { useLoaderData } from "react-router";
import { FormStepContext } from "../../context/FormContext";
import { ActiveStepForm } from "./ActiveStepForm";
import { DRAWER_WIDTH, Sidebar } from "./Sidebar";


export function MainLayout() {
    // Drawer state
    const [drawerOpen, setDrawerOpen] = React.useState(true);

    // Manage activeStep state here
    const [stepIndex, setActiveStep] = React.useState(0);

    const questionnaire = useLoaderData();
    // console.log("Data:", typeof (questionnaire), questionnaire);

    const formMethods = useForm({
        // We do custom scroll, see onError function when submit
        shouldFocusError: false,
    })

    // Set the FormStepContext value
    const stepContext = {
        setActiveStep,
        currentStep: questionnaire.document.steps[stepIndex],
        stepIndex: stepIndex,
        isFirst: stepIndex === 0,
        isLast: stepIndex === questionnaire.document.steps.length - 1,
    };

    return (
        <Box sx={{ display: 'flex' }}>
            <AppBar position="fixed" open={drawerOpen}>
                <Toolbar>
                    <IconButton
                        color="inherit"
                        aria-label="open drawer"
                        onClick={() => setDrawerOpen(!drawerOpen)}
                        edge="start"
                        sx={[
                            { marginRight: 5 },
                            drawerOpen && { display: 'none' },
                        ]}
                    >
                        <MenuIcon />
                    </IconButton>
                    <Typography variant="h6" noWrap component="div">
                        {questionnaire.name}
                    </Typography>
                </Toolbar>
            </AppBar>
            <Sidebar
                steps={questionnaire.document.steps}
                activeStep={stepIndex}
                drawerOpen={drawerOpen}
                setDrawerOpen={setDrawerOpen}
            />
            <Box
                component="main"
                sx={{
                    marginTop: "64px",
                    p: 2,
                }}
            >
                <FormStepContext.Provider value={stepContext}>
                    <FormProvider {...formMethods}>
                        <ActiveStepForm />
                    </FormProvider>
                </FormStepContext.Provider>
            </Box>
        </Box>
    );
}


interface AppBarProps extends MuiAppBarProps {
    open?: boolean;
}


const AppBar = styled(MuiAppBar, {
    shouldForwardProp: (prop) => prop !== 'open',
})<AppBarProps>(({ theme }) => ({
    zIndex: theme.zIndex.drawer + 1,
    transition: theme.transitions.create(['width', 'margin'], {
        easing: theme.transitions.easing.sharp,
        duration: theme.transitions.duration.leavingScreen,
    }),
    variants: [
        {
            props: ({ open }) => open,
            style: {
                marginLeft: DRAWER_WIDTH,
                width: `calc(100% - ${DRAWER_WIDTH}px)`,
                transition: theme.transitions.create(['width', 'margin'], {
                    easing: theme.transitions.easing.sharp,
                    duration: theme.transitions.duration.enteringScreen,
                }),
            },
        },
    ],
}));