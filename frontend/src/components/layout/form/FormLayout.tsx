import ExitToAppIcon from '@mui/icons-material/ExitToApp';
import MenuIcon from '@mui/icons-material/Menu';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import SaveIcon from '@mui/icons-material/Save';
import MuiAppBar from '@mui/material/AppBar';
import Box from '@mui/material/Box';
import IconButton from '@mui/material/IconButton';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import React from 'react';

import type { AppBarProps as MuiAppBarProps } from '@mui/material/AppBar';
import { styled } from '@mui/material/styles';
import type { SubmitErrorHandler, SubmitHandler, UseFormProps } from 'react-hook-form';
import { FormProvider, useForm, useFormState } from 'react-hook-form';
import { useLoaderData } from 'react-router';
import { ApiManager } from '../../../context/ApiManager';
import { DRAWER_WIDTH } from '../../../context/Constants';
import { LocalStorage } from '../../../context/LocalStorage';
import type { IAnswers, IApplicationData } from '../../../context/types/Application';
import type { AsyncVoidAction, NumberedBooleanObj } from '../../../context/types/Generic';
import type { IQuestionnaire, IQuestionnaireData } from '../../../context/types/Questionnaire';
import { handleApiError, scrollToTop } from '../../../context/Utils';
import { FormActiveStep } from './FormActiveStep';
import { FormReviewPage } from './FormReviewPage';
import { FormSidebar } from './FormSidebar';


export const FormLayout = () => {
    // Fetch application and questionnaire from API
    const { app, questionnaire } =
        useLoaderData<{ app: IApplicationData, questionnaire: IQuestionnaireData }>();

    // Load stored answers from local storage
    // const storedAnswers = React.useMemo<IAnswers>(
    //     () => LocalStorage.getAnswers(app.key), []
    // );

    // console.log("Stored answers:", storedAnswers);

    // Drawer state
    const [drawerOpen, setDrawerOpen] = React.useState<boolean>(true);

    // Manage activeStep state here
    const [stepIndex, setActiveStep] = React.useState<number>(0);

    // Manage completed steps
    const [completedSteps, setCompleted] = React.useState<NumberedBooleanObj>({});

    // Form methods
    const formMethods = useForm<IAnswers>({
        defaultValues: app.document.answers,
        // We do custom scroll, see onError function when submit
        shouldFocusError: false,
    } as UseFormProps<IAnswers>);

    // Form state (subscribed version)
    const {
        isDirty,
        // dirtyFields,
    } = useFormState({ control: formMethods.control });
    // console.log("isDirty:", isDirty, dirtyFields)

    const saveAnswers = async (answers?: IAnswers) => {
        // No changes to save
        if (!isDirty) return;

        answers = answers || formMethods.getValues();
        await _doSaveAnswers(app.key, app.document.schema_version, answers);

        // Reset the form state with the saved answers - not dirty anymore
        formMethods.reset(answers);
    };

    const handleSubmit = (nextStep: React.SetStateAction<number>): AsyncVoidAction => {
        const onValid: SubmitHandler<IAnswers> = async (answers: IAnswers) => {
            // Set the current step as completed
            setCompleted((completed) => ({
                ...completed,
                [stepIndex]: true,
            }));
            // Save answers via API
            await saveAnswers(answers);
            // Set the new active step
            setActiveStep(nextStep);
        }

        const onError: SubmitErrorHandler<IAnswers> = async (errors) => {
            // Set the current step as failed
            setCompleted((completed) => ({
                ...completed,
                [stepIndex]: false,
            }));
            // Call the actual error handler
            return onInvalid(errors);
        }

        console.log("completedSteps:", completedSteps)

        // Return the callable function for triggering validation, 
        // then to switch to the given step if validation is successful
        return formMethods.handleSubmit(onValid, onError);
    }

    // Account menu state and handlers
    const [menuAnchorEl, setMenuAnchorEl] = React.useState<null | HTMLElement>(null);

    // Change page title
    React.useEffect(() => {
        document.title = `${app.questionnaire_name} : DBCA Authorisations`;
    }, [app.questionnaire_name]);

    // Scroll to top when step changes
    React.useEffect(() => scrollToTop(), [stepIndex]);

    // Warn users trying to close or reload with unsaved changes
    React.useEffect(() => {
        const handleBeforeUnload = (event: BeforeUnloadEvent) => {
            if (isDirty) {
                event.preventDefault();
                // Modern browsers often ignore custom messages for 
                // security reasons and display a generic message.
                return (event.returnValue = ''); // Some browsers require returnValue to be set
            }
        };
        window.addEventListener('beforeunload', handleBeforeUnload);
        return () => window.removeEventListener('beforeunload', handleBeforeUnload);
    }, [isDirty]);

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
                        {app.questionnaire_name}
                    </Typography>
                    <AccountMenu
                        anchorEl={menuAnchorEl}
                        setAnchorEl={setMenuAnchorEl}
                        isDirty={isDirty}
                        saveAnswers={saveAnswers}
                    />
                </Toolbar>
            </AppBar>
            <FormSidebar
                drawerOpen={drawerOpen}
                setDrawerOpen={setDrawerOpen}
                steps={questionnaire.document.steps}
                activeStep={stepIndex}
                handleSubmit={handleSubmit}
                completedSteps={completedSteps}
            />
            <Box component="main" sx={{ marginTop: "64px", p: 2 }}>
                <FormProvider {...formMethods}>
                    <FormLayoutContent
                        handleSubmit={handleSubmit}
                        questionnaire={questionnaire.document}
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


const AccountMenu = ({
    anchorEl, setAnchorEl,
    isDirty,
    saveAnswers,
}: {
    anchorEl: null | HTMLElement;
    setAnchorEl: React.Dispatch<React.SetStateAction<null | HTMLElement>>;
    isDirty: boolean;
    saveAnswers: () => Promise<void>;
}) => {
    const handleMenu = (event: React.MouseEvent<HTMLElement>) => setAnchorEl(event.currentTarget);
    const handleClose = () => setAnchorEl(null);

    return (
        <Box sx={{ marginLeft: 'auto' }}>
            <IconButton
                size="large"
                aria-label="account of current user"
                aria-controls="menu-appbar"
                aria-haspopup="true"
                onClick={handleMenu}
                color="inherit"
            >
                <MoreVertIcon />
            </IconButton>
            <Menu
                id="menu-appbar"
                anchorEl={anchorEl}
                anchorOrigin={{
                    vertical: 'bottom',
                    horizontal: 'right',
                }}
                keepMounted
                transformOrigin={{
                    vertical: 'top',
                    horizontal: 'right',
                }}
                open={Boolean(anchorEl)}
                onClose={handleClose}
                sx={{
                    '& .MuiMenuItem-root': { gap: 1.5 }
                    , '& .MuiSvgIcon-root': { fontSize: 'inherit' }
                }}
            >
                <MenuItem
                    disabled={!isDirty}
                    onClick={() => {
                        saveAnswers();
                        handleClose();
                    }}
                >
                    <SaveIcon /> Save
                </MenuItem>
                <MenuItem
                    onClick={() => {
                        // Assuming we're in a popup window
                        window.close();

                        // If there are unsaved changes and user cancels the closing...
                        // do nothing.
                        // if (!window.closed) { }
                    }}
                >
                    <ExitToAppIcon /> Exit
                </MenuItem>
            </Menu>
        </Box>
    )
}


const FormLayoutContent = ({
    handleSubmit,
    questionnaire, stepIndex,
}: {
    handleSubmit: (nextStep: React.SetStateAction<number>) => AsyncVoidAction,
    questionnaire: IQuestionnaire;
    stepIndex: number;
}) => {

    // We are on the review page
    if (stepIndex === questionnaire.steps.length) {
        return (
            <FormReviewPage questionnaire={questionnaire} />
        );
    }

    return (
        <FormActiveStep
            handleSubmit={handleSubmit}
            currentStep={questionnaire.steps[stepIndex]}
            stepIndex={stepIndex}
        />
    );
}


const _doSaveAnswers = async (
    key: string,
    version: string,
    answers: IAnswers,
) => {
    // Check if we have internet connection
    if (window.navigator.onLine) {
        const response = await ApiManager.updateApplication(key, version, answers)
            // Successfully save to API    
            .then((resp) => {
                // TODO: Clear the local storage
                console.log("Saved answers to API:", resp)
                return resp;
            })
            // Display error to user
            .catch(handleApiError);

        // Something went wrong with the API call, save to local storage
        if (!response) {
            console.warn("Failed to save answers to API, saving to local storage");
            LocalStorage.setAnswers(key, answers);
        }
    }
    // We are offline
    else {
        // Save answers to local storage
        console.log("Offline... saving answers to local storage");
        LocalStorage.setAnswers(key, answers);
    }
}

// Do custom scroll and focus because ...
// MUI wraps input elements in many layers and default behaviour is buggy
const onInvalid: SubmitErrorHandler<IAnswers> = (errors) => {
    const firstErrorField = Object.keys(errors)[0];
    // console.log('errors:', errors)

    // Try to find a container with the id
    const errorElement = document.getElementById(`q-${firstErrorField}`) as HTMLElement;

    if (errorElement) {
        errorElement.scrollIntoView({ behavior: "smooth", block: "center" });

        // Only focus if tabIndex is not -1 
        // (skip components that are not meant to be focused)
        if (typeof errorElement.focus === "function" && errorElement.tabIndex !== -1)
            errorElement.focus();
    }
}
