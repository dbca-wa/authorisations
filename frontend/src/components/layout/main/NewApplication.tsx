import CreateOutlinedIcon from '@mui/icons-material/CreateOutlined';
import React from "react";

import { Box, Button, Card, List, ListItem, Typography } from "@mui/material";
import { AxiosError } from 'axios';
import { Link, useLoaderData, useNavigate, type NavigateFunction } from "react-router";
import { ApiManager } from '../../../context/ApiManager';
import DialogProvider, { useDialog, type DialogOptions } from '../../../context/Dialogs';
import { finalisedStatuses, type IApplicationData } from "../../../context/types/Application";
import type { IQuestionnaireData } from "../../../context/types/Questionnaire";
import { openNewTab } from '../../../context/Utils';
import { EmptyStateComponent } from "./EmptyState";


export const NewApplication = () => {
    // const config = ConfigManager.get('');
    // console.log("Config:", config)

    const questionnaires = useLoaderData<IQuestionnaireData[]>();
    // console.log('Questionnaires:', questionnaires);

    // Creating a new application in progress state
    const [inProgress, setInProgress] = React.useState<string>("");

    return (
        <Box className="p-8 min-w-4xl max-w-7xl">
            <Typography variant="h4" gutterBottom>
                Start a New Application
            </Typography>
            <p>Select a questionnaire to start a new application.</p>
            {questionnaires.length === 0 ? <EmptyStateComponent /> :
                <DialogProvider>
                    <List>
                        {questionnaires.map((q) =>
                            <Questionnaire
                                key={q.slug}
                                questionnaire={q}
                                inProgress={inProgress}
                                setInProgress={setInProgress}
                            />)}
                    </List>
                </DialogProvider>
            }
        </Box>
    );
}

/** Display a MUI card the given questionnaire with a link to start a new application for it */
const Questionnaire = ({
    questionnaire, inProgress, setInProgress,
}: {
    questionnaire: IQuestionnaireData;
    inProgress: string;
    setInProgress: React.Dispatch<React.SetStateAction<string>>;
}) => {
    const localDate = new Date(questionnaire.created_at).toLocaleDateString()
    const navigate: NavigateFunction = useNavigate();
    const { showDialog, hideDialog } = useDialog();

    return (
        <ListItem sx={{ marginBottom: 2 }}>
            <Card className="p-8 w-full" elevation={4} sx={{ borderRadius: 2 }}>
                <Typography variant="h6">{questionnaire.name}</Typography>
                <Typography variant="subtitle2" color="textSecondary" gutterBottom>
                    Last updated: {localDate} (v{questionnaire.version})
                </Typography>
                <Typography variant="body1" color="textPrimary" gutterBottom>
                    {questionnaire.description}
                </Typography>
                <Box display="flex" justifyContent="flex-end" mt={2}>
                    <Button
                        variant="outlined"
                        color="info"
                        loadingPosition='start'
                        loading={inProgress === questionnaire.slug}
                        disabled={Boolean(inProgress)}
                        startIcon={<CreateOutlinedIcon />}
                        onClick={() => startApplication({
                            questionnaire,
                            setInProgress,
                            navigate,
                            showDialog, hideDialog,
                        })}
                    >
                        Start Application
                    </Button>
                </Box>
            </Card>
        </ListItem>
    );
}


const createNewApplication = async (
    questionnaire_slug: string,
    navigate: NavigateFunction,
) => {
    // Do create a new application and redirect to it
    const newApplication: IApplicationData | null = await ApiManager.createApplication(questionnaire_slug)
        .catch((error: AxiosError) => {
            console.error('Error creating application:', error);
            alert('[Warning dialog goes here] Failed to create an application. Please try again later.')
            return null;
        });

    if (newApplication === null) {
        return;
    }

    // // console.log("Created new application:", newApplication)
    openNewTab(`/a/${newApplication.key}`, newApplication.key);

    navigate('/my-applications', { viewTransition: true });
}

const startApplication = async ({
    questionnaire, setInProgress, navigate,
    showDialog, hideDialog,
}: {
    questionnaire: IQuestionnaireData;
    setInProgress: React.Dispatch<React.SetStateAction<string>>;
    navigate: NavigateFunction;
    showDialog: (options: DialogOptions) => void;
    hideDialog: () => void;
}) => {
    setInProgress(questionnaire.slug);

    // Check if there is already an application in progress for this questionnaire
    const existingApplications: IApplicationData[] | null = await ApiManager.fetchApplications()
        .catch((error: AxiosError) => {
            console.error('Error fetching applications:', error);
            alert("[Warning dialog goes here] Failed to fetch existing applications. Please try again later.");
            return null;
        })

    // Stop progress if fetching applications failed
    if (existingApplications === null) {
        setInProgress("");
        return;
    }

    // Find in-progress applications
    const inProgressApplication = existingApplications.find((app: IApplicationData) =>
        app.questionnaire_slug === questionnaire.slug && !finalisedStatuses.includes(app.status)
    );

    console.log("Existing applications:", existingApplications);

    if (inProgressApplication) {
        // If there is an in-progress application, display the warning dialog
        // console.log("inProgressApplication:", inProgressApplication);
        console.warn("You already have an in-progress application for this questionnaire.");
        // alert('[Warning dialog goes here] You already have an in-progress application..')

        showDialog({
            title: "Create a new one?",
            content: <>
                <Typography>You already have <Link to="/my-applications">application(s)</Link> that
                    are in-progress for this questionnaire. </Typography><br />
                <Typography>Are you sure you want to proceed and create a new one?</Typography>
            </>,
            actions: (
                <>
                    <Button onClick={() => {
                        hideDialog();
                        setInProgress("");
                    }}>Cancel</Button>
                    <Button onClick={async () => {
                        console.log("Confirmed!");
                        await createNewApplication(questionnaire.slug, navigate);
                    }}>
                        Confirm
                    </Button>
                </>
            )
        });
    }
    // No active application of this kind
    else {
        await createNewApplication(questionnaire.slug, navigate);
    }

    // setInProgress("");

    // await sleep(3000);
    // console.log("Redirecting to the my applications page...")
    // navigate('/my-applications', { viewTransition: true });
}