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
import _ from 'underscore';

import type { AlertColor } from '@mui/material/Alert';
import type { AppBarProps as MuiAppBarProps } from '@mui/material/AppBar';
import { styled } from '@mui/material/styles';
import type { AxiosError } from 'axios';
import type { FieldErrors, SubmitErrorHandler, SubmitHandler, UseFormProps } from 'react-hook-form';
import { FormProvider, useForm, useFormState } from 'react-hook-form';
import { useLoaderData } from 'react-router';
import { ApiManager } from '../../../context/ApiManager';
import { DRAWER_WIDTH } from '../../../context/Constants';
import { LocalStorage } from '../../../context/LocalStorage';
import { useSnackbar } from '../../../context/Snackbar';
import type { IApplicationAttachment, IApplicationData, IFormAnswers, IFormDocument } from '../../../context/types/Application';
import type { AsyncVoidAction, NumberedBooleanObj } from '../../../context/types/Generic';
import type { IQuestionnaire, IQuestionnaireData } from '../../../context/types/Questionnaire';
import { scrollToTop } from '../../../context/Utils';
import { FormActiveStep } from './FormActiveStep';
import { FormReviewPage } from './FormReviewPage';
import { FormSidebar } from './FormSidebar';


export const FormLayout = () => {
    // Fetch application and questionnaire from API
    const { app, questionnaire, attachments } =
        useLoaderData<{
            app: IApplicationData,
            questionnaire: IQuestionnaireData,
            attachments: IApplicationAttachment[]
        }>();

    // Load stored answers from local storage
    // const storedAnswers = React.useMemo<IFormAnswers>(
    //     () => LocalStorage.getFormState(app.key), []
    // );
    ``
    // console.log("Stored answers:", storedAnswers);

    // Drawer open/close state
    const [drawerOpen, setDrawerOpen] = React.useState<boolean>(true);

    // Can the user edit the form?
    const [userCanEdit, setUserCanEdit] = React.useState<boolean>(app.status === "DRAFT");

    // Current active step index (or the review page if not editable)
    const [activeStep, setActiveStep] = React.useState<number>(
        userCanEdit ? app.document.active_step : questionnaire.document.steps.length
    );

    const { showSnackbar } = useSnackbar();

    // Manage completed steps
    const [validatedSteps, setValidSteps] = React.useState<NumberedBooleanObj>(
        // Calculate initial state from application document
        app.document.steps.reduce((acc, step, index) => {
            if (step.is_valid !== null)
                acc[index] = step.is_valid;
            return acc;
        }, {} as NumberedBooleanObj)
    );

    // Form methods
    const formMethods = useForm<IFormAnswers>({
        // Generate default values based on application document
        defaultValues: app.document.steps.reduce((acc, step, index) => {
            acc[index] = step.answers ?? {};
            return acc;
        }, {} as IFormAnswers),
        // We do custom scroll, see `onInvalid` function while submit
        shouldFocusError: false,
    } as UseFormProps<IFormAnswers>);

    // Form state (subscribed version)
    const {
        isDirty,
    } = useFormState({ control: formMethods.control });

    /**
     * Saves the current form answers to the API,
     * or to local storage if offline or API fails,
     * then resets the form state to not dirty.
     * @returns Promise<void>
     */
    const saveAnswers = async (
        newActiveStep?: number,
        currentValidatedSteps?: NumberedBooleanObj,
    ) => {
        // Convert form answers to document structure
        const answers: IFormAnswers = formMethods.getValues();
        const document: IFormDocument = {
            schema_version: app.document.schema_version,
            active_step: newActiveStep ?? activeStep,
            steps: questionnaire.document.steps.map((_step, index) => ({
                // Use the passed-in object first, falling back to the state variable
                is_valid: (currentValidatedSteps ?? validatedSteps)[index] ?? null,
                answers: answers[index] ?? {},
            })),
        };
        // console.log("document:", document)
        await _doSaveAnswers(app.key, document, showSnackbar);

        // Reset the form state with the saved answers - not dirty anymore
        formMethods.reset(answers);
    };

    /**
     * 
     * @param nextStep The step this form should go after successful validation.
     * @returns The callable function for triggering validation.
     * @example Go to next step on successful validation: `onSubmit={handleSubmit((prev) => prev + 1)}`
     */
    const handleSubmit = (nextStep: React.SetStateAction<number>,): AsyncVoidAction => {
        const onValid: SubmitHandler<IFormAnswers> = async (_: IFormAnswers) => {
            // Calculate the next state for validated steps
            const newValidatedSteps = { ...validatedSteps };
            // Watch out for the review step, which is outside the range of steps array
            if (activeStep < questionnaire.document.steps.length)
                newValidatedSteps[activeStep] = true;
            // Set the new state (for next render)
            setValidSteps(newValidatedSteps);

            // Determine the next step index
            const nextStepInt = nextStep instanceof Function ? nextStep(activeStep) : nextStep;

            // Save answers via API
            await saveAnswers(nextStepInt, newValidatedSteps);
            // Set the new active step
            setActiveStep(nextStep);
        }

        const onInvalid: SubmitErrorHandler<IFormAnswers> = async (errors: FieldErrors<IFormAnswers>) => {
            // Set the current step as failed
            setValidSteps((completed) => ({
                ...completed,
                [activeStep]: false,
            }));

            // Do custom scroll and focus because ...
            // MUI wraps input elements in many layers and default behaviour is buggy

            // We know the errors there, fetch their keys with assertive approach
            const stepKey = _.first(_.keys(errors)) as string;
            const stepErrors = (errors as any)[stepKey]!;      // assert exists
            const fieldKey = _.first(_.keys(stepErrors)) as string;
            const firstErrorField = `${stepKey}.${fieldKey}`;
            // console.log('fieldKey:', fieldKey)

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

        return formMethods.handleSubmit(onValid, onInvalid);
    }

    // Account menu state and handlers
    const [menuAnchorEl, setMenuAnchorEl] = React.useState<null | HTMLElement>(null);

    // Change page title
    React.useEffect(() => {
        document.title = `${app.questionnaire_name} : DBCA Authorisations`;
    }, [app.questionnaire_name]);

    // Scroll to top when step changes
    React.useEffect(() => scrollToTop(), [activeStep]);

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
                userCanEdit={userCanEdit}
                drawerOpen={drawerOpen}
                setDrawerOpen={setDrawerOpen}
                steps={questionnaire.document.steps}
                activeStep={activeStep}
                handleSubmit={handleSubmit}
                validatedSteps={validatedSteps}
            />
            <Box component="main" sx={{ marginTop: "64px", p: 2 }}>
                <FormProvider {...formMethods}>
                    <FormLayoutContent
                        userCanEdit={userCanEdit}
                        setUserCanEdit={setUserCanEdit}
                        handleSubmit={handleSubmit}
                        questionnaire={questionnaire.document}
                        attachments={attachments}
                        activeStep={activeStep}
                        applicationKey={app.key}
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
    userCanEdit,
    setUserCanEdit,
    handleSubmit,
    questionnaire,
    attachments,
    activeStep,
    applicationKey,
}: {
    userCanEdit: boolean;
    setUserCanEdit: React.Dispatch<React.SetStateAction<boolean>>;
    handleSubmit: (nextStep: React.SetStateAction<number>) => AsyncVoidAction,
    questionnaire: IQuestionnaire;
    attachments: IApplicationAttachment[];
    activeStep: number;
    applicationKey: string;
}) => {
    // We are on the review page
    if (activeStep === questionnaire.steps.length) {
        return (
            <FormReviewPage
                userCanEdit={userCanEdit}
                setUserCanEdit={setUserCanEdit}
                questionnaire={questionnaire}
                attachments={attachments}
                handleSubmit={handleSubmit}
                applicationKey={applicationKey}
            />
        );
    }

    return (
        <FormActiveStep
            handleSubmit={handleSubmit}
            applicationKey={applicationKey}
            currentStep={questionnaire.steps[activeStep]}
            attachments={attachments}
            activeStep={activeStep}
        />
    );
}


const _doSaveAnswers = async (
    key: string,
    document: IFormDocument,
    showSnackbar: (message: React.ReactNode, severity?: AlertColor) => void,
) => {
    // Check if we have internet connection
    if (window.navigator.onLine) {
        const response = await ApiManager.updateApplication(key, document)
            // Successfully save to API    
            .then((resp) => {
                // TODO: Clear the local storage
                // console.log("Saved answers to API:", resp)
                showSnackbar("Application saved", "success");
                return resp;
            })
            // Display the error message to user and log to console
            .catch((error: AxiosError) => {
                console.error('API Error:', error);
                const message = (error.response?.data as any)?.document?.[0] ?? error.message;
                showSnackbar(`Failed to save: ${message}`, "error");
                return null;
            });

        // Something went wrong with the API call, save to local storage
        if (!response) {
            console.warn("Failed to save form state to API, saving to local storage");
            LocalStorage.setFormState(key, document);
        }
    }
    // We are offline
    else {
        // Save answers to local storage
        console.log("Offline... saving answers to local storage");
        LocalStorage.setFormState(key, document);
    }
}


