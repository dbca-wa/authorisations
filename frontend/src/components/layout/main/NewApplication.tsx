import CreateOutlinedIcon from '@mui/icons-material/CreateOutlined';
import ArrowDownwardRoundedIcon from '@mui/icons-material/ArrowDownwardRounded';
import LaunchIcon from '@mui/icons-material/Launch';
import LinkOutlinedIcon from '@mui/icons-material/LinkOutlined';
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import Checkbox from "@mui/material/Checkbox";
import FormControlLabel from "@mui/material/FormControlLabel";
import IconButton from '@mui/material/IconButton';
import Link from '@mui/material/Link';
import Stack from "@mui/material/Stack";
import Tab from "@mui/material/Tab";
import Tabs from "@mui/material/Tabs";
import Typography from "@mui/material/Typography";
import React from "react";

import { AxiosError } from 'axios';
import { useLoaderData, useNavigate, type NavigateFunction } from "react-router";
import { ApiManager } from '../../../context/ApiManager';
import { useDialog, useResolvedPromise, useSnackbar } from '../../../context/Hooks';
import { TurnstileManager } from '../../../context/TurnstileManager';
import { activeStatuses, type IApplicationData } from "../../../context/types/Application";
import type { LoaderData } from '../../../context/types/Generic';
import type { IAuthorisationProcess, IQuestionnaireData } from "../../../context/types/Questionnaire";
import { openNewTab } from '../../../context/Utils';
import { EmptyStateComponent } from "./EmptyState";
import { LoadingState } from "./LoadingState";

// ============================================================================
// Utility Functions & Interfaces
// ============================================================================

/**
 * Generates a hash identifier for a questionnaire in the format: `{process_slug}-{questionnaire_code}`.
 * Used for creating permanent links to specific questionnaire types within the new application page.
 * @param questionnaire The questionnaire data object
 * @returns Hash string suitable for use in window.location.hash
 */
const generateQuestionnaireHash = (questionnaire: IQuestionnaireData): string => {
    return `${questionnaire.process_slug}-${questionnaire.code}`;
};


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

// ============================================================================
// Application Flow Functions
// ============================================================================

/**
 * Collection notice dialog with consent acknowledgement and Turnstile verification.
 *
 * Renders the S717 collection notice content with a Turnstile verification widget,
 * acknowledgement checkbox, and action buttons. The checkbox and "I agree" button
 * are disabled until Turnstile verification succeeds and user acknowledges.
 */
const CollectionNoticeDialog = ({
    onConfirmed,
    onDeclined,
}: {
    onConfirmed: (userAcknowledged: boolean, turnstileToken: string) => void;
    onDeclined: () => void;
}) => {
    const [isAccepted, setIsAccepted] = React.useState<boolean>(false);
    const [turnstileLoading, setTurnstileLoading] = React.useState<boolean>(true);
    const [turnstileError, setTurnstileError] = React.useState<string | null>(null);
    const [turnstileToken, setTurnstileToken] = React.useState<string | null>(null);
    const [showScrollButton, setShowScrollButton] = React.useState<boolean>(true);
    const hasInitializedRef = React.useRef<boolean>(false);
    const turnstileContainerRef = React.useRef<HTMLDivElement | null>(null);
    const scrollableContentRef = React.useRef<HTMLDivElement | null>(null);

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

    const handleConfirmed = () => {
        if (!turnstileToken) {
            throw new Error("Turnstile token is missing. Cannot proceed with application creation.");
        }
        onConfirmed(isAccepted, turnstileToken);
    };

    // Scroll down indicator button handler
    const handleScrollDown = () => {
        if (scrollableContentRef.current) {
            scrollableContentRef.current.scrollBy({
                top: scrollableContentRef.current.clientHeight,
                behavior: 'smooth',
            });
        }
        setShowScrollButton(false);
    };

    // Hide the scroll down button when the user scrolls manually
    React.useEffect(() => {
        const scrollableContent = scrollableContentRef.current;
        if (!scrollableContent) return;

        const handleScroll = () => {
            setShowScrollButton(false);
        };

        scrollableContent.addEventListener('scroll', handleScroll);
        return () => {
            scrollableContent.removeEventListener('scroll', handleScroll);
        };
    }, []);

    // Determine if content is actually scrollable using ResizeObserver
    React.useEffect(() => {
        const scrollableContent = scrollableContentRef.current;
        if (!scrollableContent) return;

        const resizeObserver = new ResizeObserver(() => {
            const isScrollable = scrollableContent.scrollHeight > scrollableContent.clientHeight;
            setShowScrollButton(isScrollable);
        });

        resizeObserver.observe(scrollableContent);

        return () => {
            resizeObserver.disconnect();
        };
    }, []);


    return (
        <>
            <Box
                ref={scrollableContentRef}
                className="max-h-[60vh] overflow-y-auto border-b border-gray-300"
            >
                <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                    The Department of Biodiversity, Conservation and Attractions (DBCA) collects personal information to:
                </Typography>
                <ul className="pl-6 mb-4 text-inherit list-disc">
                    <li>
                        <Typography variant="body2" color="textSecondary">
                            receive, assess and manage animal ethics submissions and approvals in accordance with section 8 of the <em>Animal Welfare Act 2002</em> (WA) (AW Act);
                        </Typography>
                    </li>
                    <li>
                        <Typography variant="body2" color="textSecondary">
                            assess and determine applications made under sections 40 and 45 of the <em>Biodiversity Conservation Act 2016</em> (WA) (BC Act);
                        </Typography>
                    </li>
                    <li>
                        <Typography variant="body2" color="textSecondary">
                            assess and determine applications made under regulation 89 of the <em>Conservation and Land Management Regulations 2002</em> (WA) (CALM Regulations);
                        </Typography>
                    </li>
                    <li>
                        <Typography variant="body2" color="textSecondary">
                            administer, monitor and enforce other authorisations, permits and approvals that it issues;
                        </Typography>
                    </li>
                    <li>
                        <Typography variant="body2" color="textSecondary">
                            communicate with applicants, nominees, researchers, licence holders and authorised representatives regarding applications, approvals, compliance matters or related enquiries; and
                        </Typography>
                    </li>
                    <li>
                        <Typography variant="body2" color="textSecondary">
                            meet its statutory obligations for record-keeping, reporting, audit and regulatory compliance.
                        </Typography>
                    </li>
                </ul>
                <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                    The personal information collected may include names, contact details, organisational affiliation, role details and other information necessary to assess applications and issue lawful authority for activities.
                </Typography>
                <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                    DBCA may share this information:
                </Typography>
                <ul className="pl-6 mb-4 text-inherit list-disc">
                    <li>
                        <Typography variant="body2" color="textSecondary">
                            internally within DBCA for assessment, decision-making, compliance, audit and operational purposes;
                        </Typography>
                    </li>
                    <li>
                        <Typography variant="body2" color="textSecondary">
                            with relevant advisory bodies, committees or experts (including the <em>Animal Ethics Committee</em>) for the purpose of evaluating applications and submissions;
                        </Typography>
                    </li>
                    <li>
                        <Typography variant="body2" color="textSecondary">
                            with the <em>Department of Primary Industries and Regional Development</em> (DPIRD) for the purpose of assessing and determining exemptions under section 7 of the <em>Fish Resources Management Act 1994</em> (WA) (FRMA Act), including in some cases the application of biodiversity conservation conditions for the purposes of section 7(2)(b) of the BC Act; and
                        </Typography>
                    </li>
                    <li>
                        <Typography variant="body2" color="textSecondary">
                            with other Western Australian public sector agencies or oversight bodies where required or authorised under the <em>Privacy and Responsible Information Sharing Act 2024</em> (WA) (PRIS Act), the BC Act, the AW Act, the <em>Conservation and Land Management Act 1984</em> (WA) (CALM Act), or any other written law.
                        </Typography>
                    </li>
                </ul>
                <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                    You are required to provide this information where it is necessary to enable DBCA to assess applications and submissions and to perform its statutory functions under the BC Act, the AW Act, the CALM Act, the CALM Regulations and to support DPIRD's statutory functions under the FRMA Act.
                </Typography>
                <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                    If you choose not to provide the required personal information, DBCA may be unable to assess your application or submission, issue an approval or authorisation, or progress the matter further.
                </Typography>
                <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                    DBCA will handle all personal information in accordance with the PRIS Act and DBCA's Privacy Policy.
                </Typography>
                <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                    For further details on how DBCA manages your personal information, please refer to <Link href="https://www.dbca.wa.gov.au/privacy" target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1">DBCA's Privacy Policy<LaunchIcon fontSize="inherit" /></Link>.
                </Typography>
                <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                    If you have any questions about how your personal information will be handled, or if you would like to access or correct your personal information, please contact DBCA at email <Link href="mailto:privacy@dbca.wa.gov.au">privacy@dbca.wa.gov.au</Link>.
                </Typography>

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

                {/* Collection notice acknowledgement checkbox is disabled until verification succeeds */}
                <FormControlLabel
                    control={(
                        <Checkbox
                            checked={isAccepted && isVerificationComplete}
                            onChange={(_event, checked) => isVerificationComplete && setIsAccepted(checked)}
                            disabled={!isVerificationComplete}
                        />
                    )}
                    label="I acknowledge the above information and that DBCA will handle my personal information in accordance with applicable privacy laws and its Privacy Policy."
                />

                {/* Scroll down indicator button - sticky at bottom, disappears after click */}
                {showScrollButton && (
                    <Box className="sticky bottom-0 mx-auto w-fit pb-4">
                        <IconButton
                            color="primary"
                            onClick={handleScrollDown}
                            size="medium"
                            sx={{ borderColor: 'primary.main', backgroundColor: theme => theme.palette.background.default }}
                            className="border! animate-bounce"
                            disableRipple
                        >
                            <ArrowDownwardRoundedIcon />
                        </IconButton>
                    </Box>
                )}
            </Box>

            {/* Action buttons */}
            <Stack direction="row" sx={{ justifyContent: "space-between", mt: 2 }}>
                <Button variant="outlined" color="inherit" onClick={onDeclined}>
                    I decline
                </Button>
                <Button
                    variant="contained"
                    color="primary"
                    disabled={!isAccepted || !isVerificationComplete}
                    onClick={handleConfirmed}
                >
                    I agree
                </Button>
            </Stack>
        </>
    );
}


// ============================================================================
// Component Hierarchy (Child to Parent)
// ============================================================================

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

/**
 * Questionnaire displays a single questionnaire form for creating a new application.
 * Provides metadata (steps, sections, questions count), a button to start the application,
 * and a permalink button that copies a link to this questionnaire to the clipboard.
 */
const Questionnaire = ({
    questionnaire, inProgress, setInProgress,
}: {
    questionnaire: IQuestionnaireData;
    inProgress: boolean;
    setInProgress: React.Dispatch<React.SetStateAction<boolean>>;
}) => {
    const localDate = formatDate(questionnaire.updated_at)
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

    /**
     * Copies a permanent link of this questionnaire to the clipboard.
     */
    const copyLinkToClipboard = () => {
        const hash = generateQuestionnaireHash(questionnaire);
        const link = `${window.location.origin}/new-application#${hash}`;

        navigator.clipboard.writeText(link).then(() => {
            showSnackbar("Link copied to clipboard", "info");
        }).catch(() => {
            showSnackbar("Failed to copy link", "error");
        });
    };


    /**
     * Starts a new application process after checking for same type existing in-progress applications
     * and showing a collection notice dialog for consent and Turnstile verification.
     */
    const onStartApplication = async () => {
        setInProgress(true);

        // Fetch existing applications to check for in-progress applications of the same type.
        const existingApplications: IApplicationData[] | null = await ApiManager.fetchApplications()
            .catch((error: AxiosError) => {
                showSnackbar(
                    "Failed to fetch existing applications, please try again later. If problem persists, contact support.",
                    "error",
                );
                console.error('Error fetching applications:', error);
                return null;
            })

        // Error fetching existing applications, stop the flow and reset inProgress state.
        if (existingApplications === null) {
            setInProgress(false);
            return;
        }

        if (import.meta.env.DEV) {
            console.debug("Existing same process applications:", existingApplications);
        }

        // Find any existing applications that are in-progress for the same process type.
        const inProgressApplication = existingApplications.find((app: IApplicationData) =>
            app.process_slug === questionnaire.process_slug && activeStatuses.includes(app.status)
        );

        /**
         * Opens the collection notice consent window and proceeds to create a new application 
         * if Turnstile verification succeeds and the user acknowledges the collection notice.
         */
        const showCollectionNoticeDialog = () => {
            const onConfirmed = (userAcknowledged: boolean, turnstileToken: string) => {
                ApiManager.createApplication({
                    processSlug: questionnaire.process_slug,
                    questionnaireId: questionnaire.id,
                    questionnaireCode: questionnaire.code,
                    questionnaireVersion: questionnaire.version,
                    collectionNoticeAgreed: userAcknowledged,
                    turnstileToken,
                }).then((newApplication) => {
                    openNewTab(`/a/${newApplication.key}`, newApplication.key);
                    navigate('/my-applications', { viewTransition: true });
                    return true;
                }).catch((error: AxiosError) => {
                    console.error('Error creating application:', error);
                    showSnackbar(
                        "Failed to create an application, please try again later. If problem persists, contact support.",
                        "error",
                    );
                    return false;
                }).finally(() => {
                    hideDialog();
                    setInProgress(false);
                });
            };

            const onDeclined = () => {
                hideDialog();
                setInProgress(false);
            };

            showDialog({
                title: "Collection Notice Disclaimer",
                content: <CollectionNoticeDialog onConfirmed={onConfirmed} onDeclined={onDeclined} />,
                onClose: () => setInProgress(false),
            });
        }

        if (inProgressApplication) {
            showDialog({
                title: "Create a new application?",
                content: <>
                    <Typography>You already have <Link href="/my-applications">application(s)</Link> that
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
                                showCollectionNoticeDialog();
                            }}
                        >Confirm</Button>
                    </>
                ),
                onClose: () => setInProgress(false),
            });
        }
        else {
            showCollectionNoticeDialog();
        }
    }

    return (
        <Box sx={{ p: 1, minHeight: 300, display: "flex", flexDirection: "column", position: "relative" }}>
            <Typography variant="h6" gutterBottom>
                {questionnaire.name}
                <IconButton
                    color="inherit"
                    size="medium"
                    title="Click to copy the link to this questionnaire"
                    aria-label="Click to copy the link to this questionnaire"
                    onClick={copyLinkToClipboard}
                >
                    <LinkOutlinedIcon />
                </IconButton>
            </Typography>
            <Typography variant="body1" color="textPrimary" className="display-linebreak pb-8">
                {questionnaire.description}
            </Typography>

            <Stack direction="row" sx={{ justifyContent: "space-between", mt: "auto" }}>
                <Button
                    variant="outlined"
                    color="info"
                    loadingPosition="start"
                    loading={inProgress}
                    disabled={inProgress}
                    startIcon={<CreateOutlinedIcon />}
                    onClick={onStartApplication}
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

/**
 * ProcessGroup manages a single authorisation process and its associated questionnaires.
 */
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
    const processBoxRef = React.useRef<HTMLDivElement | null>(null);

    // Listen for hash changes and update tab selection when URL hash matches a questionnaire in this group.
    React.useEffect(() => {
        const handleHashChange = () => {
            const urlHash = window.location.hash.slice(1);
            if (!urlHash) return;

            const matchingIndex = group.questionnaires.findIndex(
                (q) => generateQuestionnaireHash(q) === urlHash
            );

            if (matchingIndex !== -1) {
                setSelectedQuestionnaireTab(matchingIndex);
                processBoxRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        };

        // Handle initial page load with hash
        handleHashChange();

        // Listen for subsequent hash changes
        window.addEventListener('hashchange', handleHashChange);

        return () => {
            window.removeEventListener('hashchange', handleHashChange);
        };
    }, [group.questionnaires]);

    // Keep tab state stable while preventing out-of-range access when questionnaire lists change.
    const safeSelectedQuestionnaireTab = Math.min(
        selectedQuestionnaireTab,
        Math.max(group.questionnaires.length - 1, 0),
    );
    const selectedQuestionnaire = group.questionnaires[safeSelectedQuestionnaireTab];

    return (
        <Box ref={processBoxRef} className="mb-8">
            <Card className="p-6" elevation={4} sx={{ borderRadius: 2 }}>
                <ProcessOverview process={group.process} />

                <Box sx={{ display: "flex", gap: 3, mt: 3 }}>
                    <Tabs
                        orientation="vertical"
                        value={safeSelectedQuestionnaireTab}
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
                                    disabled={group.questionnaires.length === 1}
                                />
                            );
                        })}
                    </Tabs>

                    {selectedQuestionnaire && (
                        <Box
                            role="tabpanel"
                            id={`questionnaire-tabpanel-${group.process.slug}-${safeSelectedQuestionnaireTab}`}
                            aria-labelledby={`questionnaire-tab-${group.process.slug}-${safeSelectedQuestionnaireTab}`}
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
        <Box className="p-8 w-full min-w-4xl lg:w-4xl xl:w-5xl 2xl:w-6xl">
            <Typography variant="h4" gutterBottom>
                Start a New Application
            </Typography>
            <Typography color="textSecondary" sx={{ mb: 4 }}>
                Create a new application for an authorisation process.
            </Typography>
            {isQuestionnairesLoading ? <LoadingState /> :
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

