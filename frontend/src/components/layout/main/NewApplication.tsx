import CreateOutlinedIcon from '@mui/icons-material/CreateOutlined';
import React from "react";

import type { AlertColor } from '@mui/material/Alert';
import { Box, Button, Card, Stack, Tab, Tabs, Typography } from "@mui/material";
import { AxiosError } from 'axios';
import { Link, useLoaderData, useNavigate, type NavigateFunction } from "react-router";
import { ApiManager } from '../../../context/ApiManager';
import DialogProvider, { useDialog, type DialogOptions } from '../../../context/Dialogs';
import { finalisedStatuses, type IApplicationData } from "../../../context/types/Application";
import type { IAuthorisationProcess, IQuestionnaireData } from "../../../context/types/Questionnaire";
import { openNewTab } from '../../../context/Utils';
import { EmptyStateComponent } from "./EmptyState";
import { useSnackbar } from '../../../context/Snackbar';

interface IProcessGroup {
    process: IAuthorisationProcess;
    questionnaires: IQuestionnaireData[];
}

const formatDate = (value: string): string => {
    return new Date(value).toLocaleDateString();
}

const getQuestionnaireProcessSlug = (questionnaire: IQuestionnaireData): string => {
    return questionnaire.slug;
}

const getQuestionnaireUiKey = (questionnaire: IQuestionnaireData): string => {
    return `${getQuestionnaireProcessSlug(questionnaire)}:${questionnaire.name}:v${questionnaire.version}`;
}

const buildProcessName = (slug: string): string => {
    return slug
        .split(/[-_]/g)
        .filter(Boolean)
        .map((chunk) => chunk.charAt(0).toUpperCase() + chunk.slice(1))
        .join(" ");
}

const buildProcesses = (questionnaires: IQuestionnaireData[]): IAuthorisationProcess[] => {
    const processMap = new Map<string, IAuthorisationProcess>();
    const longDescription = "The application process for using animals for scientific or educational purposes in Western Australia, integrating the Animal Welfare Act 2002, the Biodiversity Conservation Act 2016, and the Australian Code for the Care and Use of Animals for Scientific Purposes. It is designed to guide applicants, investigators, Animal Ethics Committee (AEC) members, and other stakeholders through the process.";

    for (const questionnaire of questionnaires) {
        const processSlug = getQuestionnaireProcessSlug(questionnaire);
        const existingProcess = processMap.get(processSlug);

        if (existingProcess) {
            existingProcess.updated_at =
                new Date(questionnaire.created_at) > new Date(existingProcess.updated_at)
                    ? questionnaire.created_at
                    : existingProcess.updated_at;
            continue;
        }

        processMap.set(processSlug, {
            slug: processSlug,
            // name: buildProcessName(processSlug),
            name: "Care and Use of Animals for Scientific Purposes",
            description: longDescription,
            sort_order: processMap.size,
            created_at: questionnaire.created_at,
            updated_at: questionnaire.created_at,
        });
    }

    return [...processMap.values()].sort((a, b) => {
        if (a.sort_order !== b.sort_order) {
            return a.sort_order - b.sort_order;
        }

        return a.name.localeCompare(b.name);
    });
}

const buildProcessGroups = (
    questionnaires: IQuestionnaireData[],
    processes: IAuthorisationProcess[],
): IProcessGroup[] => {
    return processes
        .map((group) => ({
            process: group,
            questionnaires: questionnaires
                .filter((questionnaire) => getQuestionnaireProcessSlug(questionnaire) === group.slug)
                .sort((a, b) => {
                    if (a.name !== b.name) {
                        return a.name.localeCompare(b.name);
                    }

                    return b.version - a.version;
                }),
        }))
        .filter((group) => group.questionnaires.length > 0);
}

const ProcessOverview = ({
    process,
    questionnaireCount,
}: {
    process: IAuthorisationProcess;
    questionnaireCount: number;
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

const ProcessQuestionnaires = ({
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
                    questionnaireCount={group.questionnaires.length}
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
    const questionnaires = useLoaderData<IQuestionnaireData[]>();
    const processes = React.useMemo(
        () => buildProcesses(questionnaires),
        [questionnaires],
    );
    const processGroups = React.useMemo(
        () => buildProcessGroups(questionnaires, processes),
        [questionnaires, processes],
    );

    const [inProgress, setInProgress] = React.useState<string>("");

    return (
        <Box className="p-8 min-w-4xl max-w-7xl">
            <Typography variant="h4" gutterBottom>
                Start a New Application
            </Typography>
            {questionnaires.length === 0 ? <EmptyStateComponent /> :
                <DialogProvider>
                    {processGroups.map((group) => (
                        <ProcessQuestionnaires
                            key={group.process.slug}
                            group={group}
                            inProgress={inProgress}
                            setInProgress={setInProgress}
                        />
                    ))}
                </DialogProvider>
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
    questionnaire_slug: string,
    navigate: NavigateFunction,
    showSnackbar: (message: React.ReactNode, severity?: AlertColor) => void,
) => {
    const newApplication: IApplicationData | null = await ApiManager.createApplication(questionnaire_slug)
        .catch((error: AxiosError) => {
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
    const processSlug = getQuestionnaireProcessSlug(questionnaire);
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
        app.questionnaire_slug === processSlug && !finalisedStatuses.includes(app.status)
    );

    console.debug("Existing applications:", existingApplications);

    if (inProgressApplication) {
        showDialog({
            title: "Create a new application?",
            content: <>
                <Typography>You already have <Link to="/my-applications">application(s)</Link> that
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
                            await createNewApplication(processSlug, navigate, showSnackbar);
                        }}
                    >Confirm</Button>
                </>
            ),
            onClose: () => {
                setInProgress("");
            },
        });
    }
    else {
        await createNewApplication(processSlug, navigate, showSnackbar);
    }
}
