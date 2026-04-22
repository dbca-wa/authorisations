import CreateOutlinedIcon from '@mui/icons-material/CreateOutlined';
import MuiLink from '@mui/material/Link';
import React from "react";

import { Box, Button, Card, Checkbox, FormControlLabel, Stack, Tab, Tabs, Typography } from "@mui/material";
import type { AlertColor } from '@mui/material/Alert';
import { AxiosError } from 'axios';
import { useLoaderData, useNavigate, type NavigateFunction } from "react-router";
import { ApiManager } from '../../../context/ApiManager';
import { useDialog, type DialogOptions } from '../../../context/Dialogs';
import { useSnackbar } from '../../../context/Snackbar';
import { finalisedStatuses, type IApplicationData } from "../../../context/types/Application";
import type { IAuthorisationProcess, IQuestionnaireData } from "../../../context/types/Questionnaire";
import { openNewTab } from '../../../context/Utils';
import { EmptyStateComponent } from "./EmptyState";
import type { LoaderData } from '../../../context/types/Generic';
import { useResolvedPromise } from "../../Common";

interface IProcessGroup {
    process: IAuthorisationProcess;
    questionnaires: IQuestionnaireData[];
}

const formatDate = (value: string): string => {
    return new Date(value).toLocaleDateString();
}

const getQuestionnaireUiKey = (questionnaire: IQuestionnaireData): string => {
    return `${questionnaire.process_slug}:${questionnaire.code}:v${questionnaire.version}`;
}

const buildProcessGroups = (
    processes: IAuthorisationProcess[],
    questionnaires: IQuestionnaireData[],
): IProcessGroup[] => {
    return processes
        .map((group) => ({
            process: group,
            questionnaires: questionnaires.filter((q) => q.process_slug === group.slug),
        }))
        .filter((group) => group.questionnaires.length > 0);
}

const ProcessOverview = ({
    process,
}: {
    process: IAuthorisationProcess;
}) => {
    const processImageUrl = process.image_url;
    const processImageCredit = process.image_credit;

    return (
        <>
            {processImageUrl && (
                <Box sx={{ mb: 2 }}>
                    <Box
                        component="img"
                        src={processImageUrl}
                        alt={`${process.name} image`}
                        sx={{
                            width: "100%",
                            height: 260,
                            objectFit: "cover",
                            borderRadius: 1,
                            display: "block",
                        }}
                    />
                    <Typography variant="caption" color="textSecondary" sx={{ mt: 0.5, display: "block" }}>
                        Photo credit: {processImageCredit || "TBC"}
                    </Typography>
                </Box>
            )}

            <Stack spacing={1}>
                <Typography variant="h5">{process.name}</Typography>
                <Typography variant="body1" color="textSecondary">
                    {process.description}
                </Typography>
            </Stack>
        </>
    );
}

const ProcessGroup = ({
    group,
    inProgress,
    setInProgress,
}: {
    group: IProcessGroup;
    inProgress: string;
    setInProgress: React.Dispatch<React.SetStateAction<string>>;
}) => {
    const [selectedQuestionnaireTab, setSelectedQuestionnaireTab] = React.useState<number>(0);

    React.useEffect(() => {
        if (selectedQuestionnaireTab >= group.questionnaires.length) {
            setSelectedQuestionnaireTab(0);
        }
    }, [group.questionnaires.length, selectedQuestionnaireTab]);

    const selectedQuestionnaire = group.questionnaires[selectedQuestionnaireTab];

    return (
        <Box mb={5}>
            <Card className="p-6" elevation={4} sx={{ borderRadius: 2 }}>
                <ProcessOverview
                    process={group.process}
                />

                <Box sx={{ display: "flex", gap: 3, mt: 3 }}>
                    <Tabs
                        orientation="vertical"
                        value={selectedQuestionnaireTab}
                        onChange={(_, value: number) => setSelectedQuestionnaireTab(value)}
                        aria-label={`${group.process.name} questionnaire tabs`}
                        sx={{ minWidth: 220, borderRight: 1, borderColor: "divider" }}
                    >
                        {group.questionnaires.map((questionnaire, index) => {
                            return (
                                <Tab
                                    key={getQuestionnaireUiKey(questionnaire)}
                                    label={questionnaire.name}
                                    id={`questionnaire-tab-${group.process.slug}-${index}`}
                                    aria-controls={`questionnaire-tabpanel-${group.process.slug}-${index}`}
                                    sx={{ alignItems: "flex-start", textAlign: "left" }}
                                />
                            );
                        })}
                    </Tabs>

                    {selectedQuestionnaire && (
                        <Box
                            role="tabpanel"
                            id={`questionnaire-tabpanel-${group.process.slug}-${selectedQuestionnaireTab}`}
                            aria-labelledby={`questionnaire-tab-${group.process.slug}-${selectedQuestionnaireTab}`}
                            sx={{ flex: 1, minWidth: 0 }}
                        >
                            <Questionnaire
                                questionnaire={selectedQuestionnaire}
                                inProgress={inProgress}
                                setInProgress={setInProgress}
                            />
                        </Box>
                    )}
                </Box>
            </Card>
        </Box>
    );
}

export const NewApplication = () => {
    const { processes, questionnaires: questionnairesPromise } = useLoaderData<LoaderData>();
    const [questionnaires, isQuestionnairesLoading] = useResolvedPromise<IQuestionnaireData[]>(questionnairesPromise, []);

    const processGroups: IProcessGroup[] = React.useMemo(
        () => buildProcessGroups(processes, questionnaires),
        [processes, questionnaires],
    );

    const [inProgress, setInProgress] = React.useState<string>("");

    return (
        <Box className="p-8 min-w-4xl max-w-7xl">
            <Typography variant="h4" gutterBottom>
                Start a New Application
            </Typography>
            {isQuestionnairesLoading ? <Typography>Loading questionnaires...</Typography> :
                processGroups.length === 0 ? <EmptyStateComponent /> :
                    <>
                        {processGroups.map((group) => (
                            <ProcessGroup
                                key={group.process.slug}
                                group={group}
                                inProgress={inProgress}
                                setInProgress={setInProgress}
                            />
                        ))}
                    </>
            }
        </Box>
    );
}

const Questionnaire = ({
    questionnaire, inProgress, setInProgress,
}: {
    questionnaire: IQuestionnaireData;
    inProgress: string;
    setInProgress: React.Dispatch<React.SetStateAction<string>>;
}) => {
    const localDate = formatDate(questionnaire.created_at)
    const questionnaireUiKey = getQuestionnaireUiKey(questionnaire);
    const navigate: NavigateFunction = useNavigate();
    const { showDialog, hideDialog } = useDialog();
    const { showSnackbar } = useSnackbar();

    const sectionsCount = questionnaire.document.steps.reduce((acc, step) => {
        return acc + step.sections.length;
    }, 0);

    const questionsCount = questionnaire.document.steps.reduce((acc, step) => {
        return (
            acc
            + step.sections.reduce((sectionAcc, section) => {
                return sectionAcc + section.questions.length;
            }, 0)
        );
    }, 0);

    return (
        <Box sx={{ p: 1, minHeight: 300, display: "flex", flexDirection: "column" }}>
            <Typography variant="h6" gutterBottom>{questionnaire.name}</Typography>
            <Typography variant="body1" color="textPrimary" className="display-linebreak">
                {questionnaire.description}
            </Typography>

            <Stack direction="row" sx={{ justifyContent: "space-between", mt: "auto" }}>
                <Button
                    variant="outlined"
                    color="info"
                    loadingPosition='start'
                    loading={inProgress === questionnaireUiKey}
                    disabled={Boolean(inProgress)}
                    startIcon={<CreateOutlinedIcon />}
                    onClick={() => startApplication({
                        questionnaire,
                        setInProgress,
                        navigate,
                        showDialog, hideDialog,
                        showSnackbar,
                    })}
                >Start Application</Button>
                <Box sx={{ textAlign: "right" }}>
                    <Stack direction="row" spacing={2} flexWrap="wrap" useFlexGap>
                        <Typography variant="body2" color="textSecondary">
                            Steps: <strong>{questionnaire.document.steps.length}</strong>
                        </Typography>
                        <Typography variant="body2" color="textSecondary">
                            Sections: <strong>{sectionsCount}</strong>
                        </Typography>
                        <Typography variant="body2" color="textSecondary">
                            Questions: <strong>{questionsCount}</strong>
                        </Typography>

                    </Stack>
                    <Typography variant="subtitle2" color="textSecondary">
                        Last updated: {localDate} (v{questionnaire.version})
                    </Typography>
                </Box>
            </Stack>
        </Box>
    );
}

const createNewApplication = async (
    questionnaire: IQuestionnaireData,
    navigate: NavigateFunction,
    showSnackbar: (message: React.ReactNode, severity?: AlertColor) => void,
) => {
    const newApplication: IApplicationData | null = await ApiManager.createApplication(
        questionnaire.process_slug,
        questionnaire.id,
        questionnaire.code,
        questionnaire.version,
    ).catch((error: AxiosError) => {
        showSnackbar(
            "Failed to create an application, please try again later. If problem persists, contact support.",
            "error",
        );
        console.error('Error creating application:', error);
        return null;
    });

    if (newApplication === null) {
        return;
    }

    openNewTab(`/a/${newApplication.key}`, newApplication.key);

    navigate('/my-applications', { viewTransition: true });
}

/**
 * Renders the temporary PRIS consent content and action controls before creation.
 */
const PrisConsentDialogContent = ({
    onAgree,
    onDecline,
}: {
    onAgree: () => Promise<void>;
    onDecline: () => void;
}) => {
    const [isAccepted, setIsAccepted] = React.useState<boolean>(false);

    return (
        <Box>
            <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
                Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
                Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.
                Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.
                Curabitur pretium tincidunt lacus. Nulla gravida orci a odio. Nullam varius, turpis et commodo pharetra,
                est eros bibendum elit, nec luctus magna felis sollicitudin mauris. Integer in mauris eu nibh euismod gravida.
                Duis ac tellus et risus vulputate vehicula. Donec lobortis risus a elit. Etiam tempor. Ut ullamcorper,
                ligula eu tempor congue, eros est euismod turpis, id tincidunt sapien risus a quam. Maecenas fermentum consequat mi.
                Donec fermentum. Pellentesque malesuada nulla a mi. Duis sapien sem, aliquet nec, commodo eget, consequat quis, neque.
            </Typography>

            <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                Aliquam faucibus, elit ut dictum aliquet, felis nisl adipiscing sapien, sed malesuada diam lacus eget erat.
                Cras mollis scelerisque nunc. Nullam arcu. Aliquam consequat. Curabitur augue lorem, dapibus quis,
                laoreet et, pretium ac, nisi. Aenean magna nisl, mollis quis, molestie eu, feugiat in, orci.
                In hac habitasse platea dictumst. Fusce convallis, mauris imperdiet gravida bibendum, nisl turpis suscipit mauris,
                sed placerat ipsum urna sed risus. Class aptent taciti sociosqu ad litora torquent per conubia nostra,
                per inceptos himenaeos. Praesent sapien turpis, fermentum vel, eleifend faucibus, vehicula eu, lacus.
            </Typography>

            <FormControlLabel
                control={(
                    <Checkbox
                        checked={isAccepted}
                        onChange={(_event, checked) => setIsAccepted(checked)}
                    />
                )}
                label="I have read and agree to the PRIS consent statement."
            />

            <Stack direction="row" spacing={2} sx={{ mt: 2, justifyContent: "flex-end" }}>
                <Button
                    variant="outlined"
                    color="inherit"
                    onClick={onDecline}
                >I decline</Button>
                <Button
                    variant="contained"
                    color="primary"
                    disabled={!isAccepted}
                    onClick={async () => {
                        await onAgree();
                    }}
                >I agree</Button>
            </Stack>
        </Box>
    );
}

const startApplication = async ({
    questionnaire, setInProgress, navigate,
    showDialog, hideDialog, showSnackbar,
}: {
    questionnaire: IQuestionnaireData;
    setInProgress: React.Dispatch<React.SetStateAction<string>>;
    navigate: NavigateFunction;
    showDialog: (options: DialogOptions) => void;
    hideDialog: () => void;
    showSnackbar: (message: React.ReactNode, severity?: AlertColor) => void,
}) => {
    const questionnaireUiKey = getQuestionnaireUiKey(questionnaire);
    setInProgress(questionnaireUiKey);

    const existingApplications: IApplicationData[] | null = await ApiManager.fetchApplications()
        .catch((error: AxiosError) => {
            showSnackbar(
                "Failed to fetch existing applications, please try again later. If problem persists, contact support.",
                "error",
            );
            console.error('Error fetching applications:', error);
            return null;
        })

    if (existingApplications === null) {
        setInProgress("");
        return;
    }

    const inProgressApplication = existingApplications.find((app: IApplicationData) =>
        app.process_slug === questionnaire.process_slug && !finalisedStatuses.includes(app.status)
    );

    if (import.meta.env.DEV) {
        console.debug("Existing applications:", existingApplications);
    }

    /**
     * Opens the PRIS consent window and gates application creation on acceptance.
     */
    const showPrisConsentDialog = () => {
        showDialog({
            title: "Privacy and Responsible Information Sharing Act 2024 (WA)",
            content: (
                <PrisConsentDialogContent
                    onDecline={() => {
                        hideDialog();
                        setInProgress("");
                    }}
                    onAgree={async () => {
                        await createNewApplication(questionnaire, navigate, showSnackbar)
                            .finally(() => {
                                hideDialog();
                                setInProgress("");
                            });
                    }}
                />
            ),
            onClose: () => setInProgress(""),
        });
    }

    if (inProgressApplication) {
        showDialog({
            title: "Create a new application?",
            content: <>
                <Typography>You already have <MuiLink href="/my-applications">application(s)</MuiLink> that
                    are in-progress for this authorisation.</Typography><br />
                <Typography>Are you sure you want to proceed and create a new one?</Typography>
            </>,
            actions: (
                <>
                    <Button
                        variant="outlined"
                        color="inherit"
                        onClick={() => {
                            hideDialog();
                            setInProgress("");
                        }}
                    >Cancel</Button>
                    <Button
                        variant="contained"
                        color="warning"
                        onClick={async () => {
                            hideDialog();
                            showPrisConsentDialog();
                        }}
                    >Confirm</Button>
                </>
            ),
            onClose: () => setInProgress(""),
        });
    }
    else {
        showPrisConsentDialog();
    }
}
