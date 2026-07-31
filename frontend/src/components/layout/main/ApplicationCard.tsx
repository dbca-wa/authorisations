import DeleteOutlineIcon from '@mui/icons-material/DeleteOutlined';
import DownloadIcon from '@mui/icons-material/Download';
import PlayArrowRoundedIcon from '@mui/icons-material/PlayArrowRounded';
import RestoreIcon from '@mui/icons-material/Restore';
import Alert from '@mui/material/Alert';
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import Chip from "@mui/material/Chip";
import Link from '@mui/material/Link';
import ListItem from "@mui/material/ListItem";
import Step from "@mui/material/Step";
import StepLabel from "@mui/material/StepLabel";
import Stepper from "@mui/material/Stepper";
import Tooltip from '@mui/material/Tooltip';
import React from "react";

import { ApiManager } from '../../../context/ApiManager';
import { useSnackbar } from '../../../context/Hooks';
import type { ApplicationStatus, IApplicationData } from "../../../context/types/Application";
import { terminatedStatuses } from '../../../context/types/Application';
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

/**
 * Renders an application summary card for applicants.
 * Displays process metadata, application status, and action buttons (continue, download).
 * Maintains its own display state for immediate UI updates on status changes.
 * Notifies parent via callback when application status changes (e.g., discard, revert).
 */
export const ApplicationCard = ({
    process,
    application,
    onStatusChanged,
}: {
    process?: IAuthorisationProcess;
    application: IApplicationData;
    onStatusChanged: (updatedApp: IApplicationData) => void;
}) => {
    const [displayedApplication, setDisplayedApplication] = React.useState<IApplicationData>(application);
    const { showSnackbar } = useSnackbar();
    const processName = process?.name ?? `Unknown process (${application.process_slug})`;
    const questionnaireName = `${application.questionnaire_name} (v${application.questionnaire_version})`;
    const statusCapitalised = formatStatusLabel(displayedApplication.status);
    const { createdAtRelative, updatedAtRelative } = formatRelativeDates(displayedApplication);

    const isTerminated = terminatedStatuses.includes(displayedApplication.status);
    const isDownloadable = downloadableStatuses.has(displayedApplication.status);
    const isEditable = displayedApplication.status === "DRAFT";
    const isDiscarded = displayedApplication.status === "DISCARDED";

    /**
     * Initiates the discard workflow by sending a status update request to the API.
     * Updates local display state immediately on success for instant UI feedback.
     * Triggers removal animation, then notifies parent after animation completes.
     */
    const handleDiscardClick = async () => {
        let updatedApp: IApplicationData;
        try {
            updatedApp = await ApiManager.discardApplication(displayedApplication.key);
        } catch (error: unknown) {
            showSnackbar(
                "Failed to discard application. Please try again later.",
                "error",
            );
            console.error("Error discarding application:", error);
            return;
        }

        setDisplayedApplication(updatedApp);
        showSnackbar("Application discarded.", "info");
        onStatusChanged(updatedApp);
    };

    /**
     * Initiates the revert workflow by sending a status update request to the API.
     * Updates local display state immediately on success for instant UI feedback.
     * Triggers removal animation, then notifies parent after animation completes.
     */
    const handleRevertClick = async () => {
        let updatedApp: IApplicationData;
        try {
            updatedApp = await ApiManager.revertDiscardedApplication(displayedApplication.key);
        } catch (error: unknown) {
            showSnackbar(
                "Failed to revert application. Please try again later.",
                "error",
            );
            console.error("Error reverting application:", error);
            return;
        }

        setDisplayedApplication(updatedApp);
        showSnackbar("Application reverted to draft.", "info");
        onStatusChanged(updatedApp);
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

                <Box className="my-8 w-9/10 mx-auto flex items-center min-h-20">
                    {isTerminated ? (
                        <Alert severity="info" className="w-full">
                            <strong>{isDiscarded ? 'Application Discarded' : 'Application Withdrawn'}</strong>
                        </Alert>
                    ) : (
                        <Stepper
                            activeStep={statusToActiveStep[displayedApplication.status]}
                            alternativeLabel
                            sx={(theme) => ({
                                width: '100%',
                                '& .MuiStepIcon-root': {
                                    color: theme.palette.grey[400],
                                },
                                '& .MuiStepIcon-root.Mui-active': {
                                    color: theme.palette.success.main,
                                },
                                '& .MuiStepIcon-root.Mui-completed': {
                                    color: theme.palette.success.light,
                                },
                            })}
                        >
                            {applicationSteps.map((label) => (
                                <Step key={label}>
                                    <StepLabel>{label}</StepLabel>
                                </Step>
                            ))}
                        </Stepper>
                    )}
                </Box>
                <Box className="flex gap-1 mt-2">
                    {/* Discard button on left—only for editable (DRAFT) applications. */}
                    {isEditable && (
                        <Tooltip title="Discard application" placement="bottom" arrow>
                            <Button
                                variant="outlined"
                                color="warning"
                                startIcon={<DeleteOutlineIcon />}
                                onClick={handleDiscardClick}
                            >
                                Discard
                            </Button>
                        </Tooltip>
                    )}

                    {/* Revert button on left—only for discarded applications. */}
                    {isDiscarded && (
                        <Tooltip title="Revert to draft" placement="bottom" arrow>
                            <Button
                                variant="outlined"
                                color="primary"
                                startIcon={<RestoreIcon />}
                                onClick={handleRevertClick}
                            >
                                Revert
                            </Button>
                        </Tooltip>
                    )}

                    {/* Download and Continue buttons—push to the right. */}
                    <Box className="ml-auto flex gap-1">
                        {/* Render the PDF action only for downloadable statuses. */}
                        {isDownloadable && (
                            <Tooltip title="Download application PDF" placement="bottom" arrow>
                                <Link
                                    target="_blank"
                                    rel="noopener"
                                    aria-label="Download application PDF"
                                    href={`/d/${application.key}`}
                                >
                                    <Button
                                        variant="outlined"
                                        color="primary"
                                        startIcon={<DownloadIcon />}
                                    >
                                        Download
                                    </Button>
                                </Link>
                            </Tooltip>
                        )}

                        {/* Render the continue action only for editable applications. */}
                        {isEditable && (
                            <Tooltip title="Continue editing application" placement="bottom" arrow>
                                <Link
                                    target="_blank"
                                    rel="noopener"
                                    aria-label="Continue application"
                                    onClick={() => openNewTab(`/a/${application.key}`, application.key)}
                                >
                                    <Button
                                        variant="contained"
                                        color="success"
                                        startIcon={<PlayArrowRoundedIcon />}
                                    >
                                        Continue
                                    </Button>
                                </Link>
                            </Tooltip>
                        )}
                    </Box>
                </Box>
            </Card>
        </ListItem>
    );
};