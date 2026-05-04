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
import { TurnstileManager } from '../../../context/TurnstileManager';
import { PrivacyContent } from './PrivacyPolicy';
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
    inProgress: boolean;
    setInProgress: React.Dispatch<React.SetStateAction<boolean>>;
}) => {
    const [selectedQuestionnaireTab, setSelectedQuestionnaireTab] = React.useState<number>(0);

    React.useEffect(() => {
        if (selectedQuestionnaireTab >= group.questionnaires.length) {
            setSelectedQuestionnaireTab(0);
        }
    }, [group.questionnaires.length, selectedQuestionnaireTab]);

    const selectedQuestionnaire = group.questionnaires[selectedQuestionnaireTab];

    return (
        <Box sx={{ mb: 5 }}>
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

    const [inProgress, setInProgress] = React.useState<boolean>(false);

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
    inProgress: boolean;
    setInProgress: React.Dispatch<React.SetStateAction<boolean>>;
}) => {
    const localDate = formatDate(questionnaire.created_at)
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
                    loading={inProgress}
                    disabled={inProgress}
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
                    <Stack direction="row" spacing={2} sx={{ flexWrap: "wrap" }} useFlexGap>
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

const createNewApplication = async ({
    questionnaire,
    privacyConsentAgreed,
    turnstileToken,
    navigate,
    showSnackbar,
}: {
    questionnaire: IQuestionnaireData;
    privacyConsentAgreed: boolean;
    turnstileToken: string;
    navigate: NavigateFunction;
    showSnackbar: (message: React.ReactNode, severity?: AlertColor) => void;
}) => {
    const newApplication: IApplicationData | null = await ApiManager.createApplication({
        processSlug: questionnaire.process_slug,
        questionnaireId: questionnaire.id,
        questionnaireCode: questionnaire.code,
        questionnaireVersion: questionnaire.version,
        privacyConsentAgreed,
        turnstileToken,
    }).catch((error: AxiosError) => {
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
 * Wraps the privacy notice with dialog-specific acknowledgement controls.
 *
 * The content stays reusable for standalone pages, while this component owns
 * the acceptance state required only for the application creation flow.
 * Renders a Turnstile verification widget and gates checkbox interaction on successful verification.
 */
const PrivacyConsentDialogContent = ({
    onAgree,
    onDecline,
}: {
    onAgree: (turnstileToken: string) => Promise<void>;
    onDecline: () => void;
}) => {
    const [isAccepted, setIsAccepted] = React.useState<boolean>(false);
    const [turnstileLoading, setTurnstileLoading] = React.useState<boolean>(true);
    const [turnstileError, setTurnstileError] = React.useState<string | null>(null);
    const [turnstileToken, setTurnstileToken] = React.useState<string | null>(null);
    const hasInitializedRef = React.useRef<boolean>(false);
    const turnstileContainerRef = React.useRef<HTMLDivElement | null>(null);

    /**
    * Render the Turnstile widget on component mount and wait for its callbacks
    * to report success or failure before enabling consent.
     * Uses a ref guard to prevent double-initialization in React StrictMode (development).
     */
    React.useEffect(() => {
        // Prevent running effect twice in StrictMode even in development.
        if (hasInitializedRef.current) {
            return;
        }
        hasInitializedRef.current = true;

        const initializeTurnstile = async () => {
            try {
                setTurnstileLoading(true);
                setTurnstileError(null);
                setTurnstileToken(null);

                const container = turnstileContainerRef.current;
                if (!container) {
                    setTurnstileError("Verification widget container not found.");
                    setTurnstileLoading(false);
                    return;
                }

                // Managed widgets execute during render, so rely on callbacks
                // instead of polling for a token immediately afterwards.
                await TurnstileManager.render(container, {
                    onSuccess: (token: string) => {
                        setTurnstileToken(token);
                        setTurnstileError(null);
                        setTurnstileLoading(false);
                    },
                    onError: () => {
                        setTurnstileToken(null);
                        setTurnstileError("Verification failed. Please try again.");
                        setTurnstileLoading(false);
                    },
                    onExpire: () => {
                        setTurnstileToken(null);
                        setTurnstileLoading(true);
                    },
                });
            } catch (error) {
                setTurnstileError(
                    error instanceof Error ? error.message : "Verification widget failed to initialise."
                );
                setTurnstileLoading(false);
            }
        };

        initializeTurnstile();
    }, []);

    /**
     * Checkbox is only interactive once Turnstile verification succeeds and a token is available.
     */
    const isVerificationComplete = !turnstileLoading && !turnstileError && !!turnstileToken;

    return (
        <>
            <Box sx={{ maxHeight: "60vh", overflowY: "auto", mb: 2, pr: 1 }}>
                <PrivacyContent />
            </Box>

            {/* Turnstile verification widget container with loading spinner */}
            <Box sx={{ mb: 2 }}>
                <Box sx={{ display: "flex", justifyContent: "center" }}>
                    <div ref={turnstileContainerRef} />
                </Box>
                {turnstileError && (
                    <Typography variant="body2" color="error" sx={{ mt: 1, textAlign: "center" }}>
                        Verification failed: {turnstileError}
                    </Typography>
                )}
            </Box>

            {/* Privacy acknowledgement checkbox is disabled until verification succeeds */}
            <FormControlLabel
                control={(
                    <Checkbox
                        checked={isAccepted && isVerificationComplete}
                        onChange={(_event, checked) => isVerificationComplete && setIsAccepted(checked)}
                        disabled={!isVerificationComplete}
                    />
                )}
                label="I acknowledge that DBCA will collect, use and disclose my personal information in accordance with applicable privacy laws and DBCA's Privacy Policy."
            />

            <Stack direction="row" spacing={2} sx={{ mt: 2, justifyContent: "space-between" }}>
                <Button
                    variant="outlined"
                    color="inherit"
                    onClick={onDecline}
                >I decline</Button>
                <Button
                    variant="contained"
                    color="primary"
                    disabled={!isAccepted || !isVerificationComplete}
                    onClick={async () => {
                        if (turnstileToken) {
                            await onAgree(turnstileToken);
                        }
                    }}
                >I agree</Button>
            </Stack>
        </>
    );
}

const startApplication = async ({
    questionnaire, setInProgress, navigate,
    showDialog, hideDialog, showSnackbar,
}: {
    questionnaire: IQuestionnaireData;
    setInProgress: React.Dispatch<React.SetStateAction<boolean>>;
    navigate: NavigateFunction;
    showDialog: (options: DialogOptions) => void;
    hideDialog: () => void;
    showSnackbar: (message: React.ReactNode, severity?: AlertColor) => void,
}) => {
    setInProgress(true);

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
        setInProgress(false);
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
    const showPrivacyConsentDialog = () => {
        showDialog({
            title: "Collection Notice Disclaimer",
            content: (
                <PrivacyConsentDialogContent
                    onDecline={() => {
                        hideDialog();
                        setInProgress(false);
                    }}
                    onAgree={async (turnstileToken: string) => {
                        await createNewApplication({
                            questionnaire,
                            privacyConsentAgreed: true,
                            turnstileToken,
                            navigate,
                            showSnackbar,
                        }).finally(() => {
                            hideDialog();
                            setInProgress(false);
                        });
                    }}
                />
            ),
            onClose: () => setInProgress(false),
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
                            setInProgress(false);
                        }}
                    >Cancel</Button>
                    <Button
                        variant="contained"
                        color="warning"
                        onClick={async () => {
                            hideDialog();
                            showPrivacyConsentDialog();
                        }}
                    >Confirm</Button>
                </>
            ),
            onClose: () => setInProgress(false),
        });
    }
    else {
        showPrivacyConsentDialog();
    }
}

