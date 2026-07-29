import DeleteOutlineIcon from '@mui/icons-material/DeleteOutlined';
import DownloadIcon from '@mui/icons-material/Download';
import PlayArrowRoundedIcon from '@mui/icons-material/PlayArrowRounded';
import RestoreIcon from '@mui/icons-material/Restore';
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import Chip from "@mui/material/Chip";
import Link from '@mui/material/Link';
import ListItem from "@mui/material/ListItem";
import Step from "@mui/material/Step";
import StepLabel from "@mui/material/StepLabel";
import Stepper from "@mui/material/Stepper";
import React from "react";

import { ApiManager } from '../../../context/ApiManager';
import { useSnackbar } from '../../../context/Hooks';
import type { ApplicationStatus, IApplicationData } from "../../../context/types/Application";
import type { IAuthorisationProcess } from '../../../context/types/Questionnaire';
import { openNewTab } from '../../../context/Utils';
import { ApplicationIdDisplay } from '../../Common';
import {
    downloadableStatuses,
    formatRelativeDates,
    formatStatusLabel,
} from './applicationUtils';

// Card-specific constants for application status progression display
const applicationSteps = [
    "Application",
    "Submitted",
    "Review",
    "Assessment",
    "Decision",
] as const;

const statusToActiveStep: Record<ApplicationStatus, number> = {
    DRAFT: 0,
    DISCARDED: 0,           // Terminated during drafting — never submitted.
    SUBMITTED: 1,
    WITHDRAWN: 2,           // Terminated after submission — reached review stage.
    UNDER_REVIEW: 2,
    UNDER_ASSESSMENT: 3,
    APPROVED: 4,
    APPROVED_WITH_CONDITIONS: 4,
    DEFERRED: 4,            // Decision deferred — may resume; shown at decision step.
    REJECTED: 4,
};

/** Statuses that represent a terminal negative outcome at their respective step. */
const terminatedStatuses = new Set<ApplicationStatus>(["DISCARDED", "WITHDRAWN"]);


/**
 * Renders an application summary card for applicants.
 * Displays process metadata, application status, and action buttons (continue, download).
 * Maintains its own display state for immediate UI updates on status changes.
 */
export const ApplicationCard = ({
    process,
    application,
}: {
    process?: IAuthorisationProcess;
    application: IApplicationData;
}) => {
    const [displayedApplication, setDisplayedApplication] = React.useState<IApplicationData>(application);
    const { showSnackbar } = useSnackbar();
    const processName = process?.name ?? `Unknown process (${displayedApplication.process_slug})`;
    const questionnaireName = `${displayedApplication.questionnaire_name} (v${displayedApplication.questionnaire_version})`;
    const statusCapitalised = formatStatusLabel(displayedApplication.status);
    const { createdAtRelative, updatedAtRelative } = formatRelativeDates(displayedApplication);

    const isTerminated = terminatedStatuses.has(displayedApplication.status);
    const isDownloadable = downloadableStatuses.has(displayedApplication.status);
    const isEditable = displayedApplication.status === "DRAFT";
    const isDiscarded = displayedApplication.status === "DISCARDED";

    /**
     * Initiates the discard workflow by sending a status update request to the API.
     * Updates local display state immediately on success for instant UI feedback.
     */
    const handleDiscardClick = async () => {
        try {
            await ApiManager.discardApplication(displayedApplication.key);
            setDisplayedApplication({ ...displayedApplication, status: "DISCARDED" });
            showSnackbar("Application discarded.", "info");
        } catch (error: unknown) {
            showSnackbar(
                "Failed to discard application. Please try again later.",
                "error",
            );
            console.error("Error discarding application:", error);
        }
    };

    /**
     * Initiates the revert workflow by sending a status update request to the API.
     * Updates local display state immediately on success for instant UI feedback.
     */
    const handleRevertClick = async () => {
        try {
            await ApiManager.revertDiscardedApplication(displayedApplication.key);
            setDisplayedApplication({ ...displayedApplication, status: "DRAFT" });
            showSnackbar("Application reverted to draft.", "info");
        } catch (error: unknown) {
            showSnackbar(
                "Failed to revert application. Please try again later.",
                "error",
            );
            console.error("Error reverting application:", error);
        }
    };

    return (
        <ListItem className="mb-4">
            <Card className="p-8 w-full rounded-lg!" elevation={4}>
                <ApplicationIdDisplay internalId={application.internal_id} variant="h6" />

                <Box className="flex gap-2 my-4 flex-wrap justify-around">
                    <Chip label={processName} size="small" variant="outlined" />
                    <Chip label={questionnaireName} size="small" variant="outlined" />

                    {/* Force a wrapped row break between identifier chips and status/date chips. */}
                    <Box className="basis-full h-0" />

                    <Chip label={`${statusCapitalised}`} size="small" variant="outlined" />
                    <Chip label={`Created ${createdAtRelative}`} size="small" variant="outlined" />
                    <Chip label={`Updated ${updatedAtRelative}`} size="small" variant="outlined" />
                </Box>

                <Box className="my-8 w-9/10 mx-auto">
                    <Stepper
                        activeStep={statusToActiveStep[application.status]}
                        alternativeLabel
                        sx={(theme) => ({
                            '& .MuiStepIcon-root': {
                                color: theme.palette.grey[400],
                            },
                            '& .MuiStepIcon-root.Mui-active': {
                                // Terminated applications (discarded/withdrawn) use a muted grey
                                // to signal "stopped here" without implying an error occurred.
                                color: isTerminated
                                    ? theme.palette.grey[700]
                                    : theme.palette.success.main,
                            },
                            '& .MuiStepIcon-root.Mui-completed': {
                                color: isTerminated
                                    ? theme.palette.grey[600]
                                    : theme.palette.success.light,
                            },
                        })}
                    >
                        {applicationSteps.map((label) => (
                            <Step key={label}>
                                <StepLabel>{label}</StepLabel>
                            </Step>
                        ))}
                    </Stepper>
                </Box>
                <Box className="flex gap-1 mt-2">
                    {/* Discard button on left—only for editable (DRAFT) applications. */}
                    {isEditable && (
                        <Button
                            variant="outlined"
                            color="warning"
                            loadingPosition='start'
                            loading={false}
                            disabled={false}
                            startIcon={<DeleteOutlineIcon />}
                            onClick={handleDiscardClick}
                        >
                            Discard
                        </Button>
                    )}

                    {/* Revert button on left—only for discarded applications. */}
                    {isDiscarded && (
                        <Button
                            variant="outlined"
                            color="primary"
                            loadingPosition='start'
                            loading={false}
                            disabled={false}
                            startIcon={<RestoreIcon />}
                            onClick={handleRevertClick}
                        >
                            Revert
                        </Button>
                    )}

                    {/* Download and Continue buttons—push to the right. */}
                    <Box className="ml-auto flex gap-1">
                        {/* Render the PDF action only for downloadable statuses. */}
                        {isDownloadable && (
                            <Link
                                target="_blank"
                                rel="noopener"
                                aria-label="Download application PDF"
                                href={`/d/${application.key}`}
                            >
                                <Button
                                    variant="outlined"
                                    color="primary"
                                    loadingPosition='start'
                                    loading={false}
                                    disabled={false}
                                    startIcon={<DownloadIcon />}
                                >
                                    Download
                                </Button>
                            </Link>
                        )}

                        {/* Render the continue action only for editable applications. */}
                        {isEditable && (
                            <Link
                                target="_blank"
                                rel="noopener"
                                aria-label="Continue application"
                                onClick={() => openNewTab(`/a/${application.key}`, application.key)}
                            >
                                <Button
                                    variant="contained"
                                    color="success"
                                    loadingPosition='start'
                                    loading={false}
                                    disabled={false}
                                    startIcon={<PlayArrowRoundedIcon />}
                                >
                                    Continue
                                </Button>
                            </Link>
                        )}
                    </Box>
                </Box>
            </Card>
        </ListItem>
    );
};