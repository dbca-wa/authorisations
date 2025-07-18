import MenuIcon from '@mui/icons-material/Menu';
import MuiAppBar, { type AppBarProps as MuiAppBarProps } from '@mui/material/AppBar';
import Box from "@mui/material/Box";
import IconButton from "@mui/material/IconButton";
import Toolbar from "@mui/material/Toolbar";
import Typography from "@mui/material/Typography";
import React from "react";

import { styled } from '@mui/material/styles';
import type { FieldValues, SubmitHandler, UseFormProps } from 'react-hook-form';
import { FormProvider, useForm } from 'react-hook-form';
import { useLoaderData } from "react-router";
import { AnswersManager } from '../../context/AnswersManager';
import { DRAWER_WIDTH } from '../../context/Constants';
import type { IAnswers, IQuestionnaire } from '../../context/FormTypes';
import { ActiveStepForm } from "./ActiveStepForm";
import { ReviewPage } from './ReviewPage';
import { Sidebar } from "./Sidebar";


export const MainLayout = () => {
    // Drawer state
    const [drawerOpen, setDrawerOpen] = React.useState<boolean>(true);

    // Manage activeStep state here
    const [stepIndex, setActiveStep] = React.useState<number>(0);

    // Load questionnaire data from the loader
    const questionnaireRecord = useLoaderData();

    // Load stored answers from local storage
    const storedAnswers = React.useMemo<IAnswers>(
        () => AnswersManager.getAnswers("application-id"), []
    );

    const formParams: UseFormProps<IAnswers> = {
        defaultValues: storedAnswers,
        // We do custom scroll, see onError function when submit
        shouldFocusError: false,
    };
    const formMethods = useForm<FieldValues>(formParams);

    const handleBack = (): void => {
        // Store form values before going back
        AnswersManager.setAnswers("application-id", formMethods.getValues());

        setActiveStep((prevStep) => prevStep - 1);
    };

    const handleContinue: SubmitHandler<FieldValues> = (data) => {
        console.log("Form data:", data)

        // TODO: Replace with actual application ID
        AnswersManager.setAnswers("application-id", data);

        // Next step (or the review page)
        setActiveStep((prevStep) => prevStep + 1);
    }

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
                        {questionnaireRecord.name}
                    </Typography>
                </Toolbar>
            </AppBar>
            <Sidebar
                steps={questionnaireRecord.document.steps}
                activeStep={stepIndex}
                drawerOpen={drawerOpen}
                setDrawerOpen={setDrawerOpen}
            />
            <Box component="main" sx={{ marginTop: "64px", p: 2 }}>
                <FormProvider {...formMethods}>
                    <MainLayoutContent
                        handleBack={handleBack}
                        handleContinue={handleContinue}
                        questionnaire={questionnaireRecord.document}
                        stepIndex={stepIndex}
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
    handleBack,
    handleContinue,
    questionnaire, stepIndex,
}: {
    handleBack: () => void;
    handleContinue: SubmitHandler<FieldValues>;
    questionnaire: IQuestionnaire;
    stepIndex: number;
}) => {
    // We are on the review page
    if (stepIndex === questionnaire.steps.length) {
        return (
            <ReviewPage
                questionnaire={questionnaire}
                onBack={handleBack}
            />
        );
    }

    return (
        <ActiveStepForm
            handleBack={handleBack}
            handleContinue={handleContinue}
            currentStep={questionnaire.steps[stepIndex]}
            stepIndex={stepIndex}
        />
    );
}
