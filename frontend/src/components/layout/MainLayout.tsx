import MenuIcon from '@mui/icons-material/Menu';
import MuiAppBar, { type AppBarProps as MuiAppBarProps } from '@mui/material/AppBar';
import Box from "@mui/material/Box";
import IconButton from "@mui/material/IconButton";
import Toolbar from "@mui/material/Toolbar";
import Typography from "@mui/material/Typography";
import React, { type SetStateAction } from "react";

import { styled } from '@mui/material/styles';
import { FormProvider, useForm } from 'react-hook-form';
import { useLoaderData } from "react-router";
import { AnswersManager } from '../../context/AnswersManager';
import { FormStepContext } from "../../context/FormContext";
import type { IQuestionnaire } from '../../context/FormTypes';
import { ReviewPage } from '../ReviewPage';
import { ActiveStepForm } from "./ActiveStepForm";
import { Sidebar } from "./Sidebar";
import { DRAWER_WIDTH } from '../../context/Constants';


export const MainLayout = () => {
    // Drawer state
    const [drawerOpen, setDrawerOpen] = React.useState(true);

    // Manage activeStep state here
    const [stepIndex, setActiveStep] = React.useState(0);

    // Load questionnaire data from the loader
    const questionnaire = useLoaderData();

    // Load stored answers from local storage
    const storedAnswers = React.useMemo(
        () => AnswersManager.getAnswers("application-id"), []
    );

    const formMethods = useForm({
        defaultValues: storedAnswers,
        // We do custom scroll, see onError function when submit
        shouldFocusError: false,
    });

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
            <Box component="main" sx={{ marginTop: "64px", p: 2 }}>
                <FormProvider {...formMethods}>
                    <MainLayoutContent
                        questionnaire={questionnaire.document}
                        stepIndex={stepIndex}
                        setActiveStep={setActiveStep}
                    />
                </FormProvider>
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


const MainLayoutContent = ({
    questionnaire, stepIndex, setActiveStep,
}: {
    questionnaire: IQuestionnaire;
    stepIndex: number;
    setActiveStep: (step: SetStateAction<number>) => void;
}) => {
    // We are on the review page
    if (stepIndex === questionnaire.steps.length) {
        return <ReviewPage />;
    }

    // We are on an active step form
    const stepContext = {
        setActiveStep,
        currentStep: questionnaire.steps[stepIndex],
        stepIndex,
        isFirst: stepIndex === 0,
        isLast: stepIndex === questionnaire.steps.length - 1,
    };

    return (
        <FormStepContext.Provider value={stepContext}>
            <ActiveStepForm />
        </FormStepContext.Provider>
    );
}
