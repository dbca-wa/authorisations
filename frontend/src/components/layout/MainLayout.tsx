import MenuIcon from '@mui/icons-material/Menu';
import MuiAppBar, { type AppBarProps as MuiAppBarProps } from '@mui/material/AppBar';
import Box from "@mui/material/Box";
import IconButton from "@mui/material/IconButton";
import Toolbar from "@mui/material/Toolbar";
import Typography from "@mui/material/Typography";
import React from "react";

import { styled } from '@mui/material/styles';
import { useLoaderData } from "react-router";
import { FormStepContext } from "../../context/FormContext";
import { ActiveStepForm } from "./ActiveStepForm";
import { DRAWER_WIDTH, Sidebar } from "./Sidebar";


export function MainLayout() {
    // Drawer state
    const [drawerOpen, setDrawerOpen] = React.useState(false);

    // Manage activeStep state here
    const [activeStep, setActiveStep] = React.useState(0);

    const questionnaire = useLoaderData();
    // console.log("Data:", typeof (questionnaire), questionnaire);

    // Set the FormStepContext value
    const contextValue = {
        setActiveStep,
        currentStep: questionnaire.document.steps[activeStep],
        stepIndex: activeStep,
        isFirst: activeStep === 0,
        isLast: activeStep === questionnaire.document.steps.length - 1,
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
                activeStep={activeStep}
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
                <FormStepContext.Provider value={contextValue}>
                    <ActiveStepForm />
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