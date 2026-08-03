import AttachFileIcon from '@mui/icons-material/AttachFile';
import DownloadIcon from '@mui/icons-material/Download';
import EmailIcon from '@mui/icons-material/Email';
import HistoryIcon from '@mui/icons-material/History';
import NavigateNextRoundedIcon from '@mui/icons-material/NavigateNextRounded';
import PersonIcon from '@mui/icons-material/Person';
import RestartAltRoundedIcon from '@mui/icons-material/RestartAltRounded';
import ZoomInRoundedIcon from '@mui/icons-material/ZoomInRounded';
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import Chip from "@mui/material/Chip";
import IconButton from "@mui/material/IconButton";
import Link from '@mui/material/Link';
import ListItem from "@mui/material/ListItem";
import Tooltip from "@mui/material/Tooltip";
import Typography from "@mui/material/Typography";

import { useState } from 'react';
import { ApiManager } from '../../../context/ApiManager';
import { useDialog, useResolvedPromise, useSnackbar } from '../../../context/Hooks';
import type { ApplicationStatus, IApplicationAttachment, IApplicationData } from "../../../context/types/Application";
import type { IAuthorisationProcess } from '../../../context/types/Questionnaire';
import { ApplicationIdDisplay, FileAttachmentList } from '../../Common';
import {
    formatRelativeDates,
    formatStatusLabel,
} from './applicationUtils';
import { EmptyStateComponent } from './EmptyState';
import { LoadingState } from './LoadingState';

/**
 * Dialog content component for displaying application attachments.
 * Fetches attachments on mount and displays them in a grid with download functionality.
 * Shows loading state while fetching and empty state if no attachments are available.
 */
export const AttachmentsDialogContent = ({
    application,
}: {
    application: IApplicationData;
}) => {
    const attachmentsPromise = useState(() =>
        ApiManager.getApplicationAttachments(application.key)
    )[0];
    const [attachments, isLoading] = useResolvedPromise<IApplicationAttachment[]>(
        attachmentsPromise,
        []
    );

    if (isLoading) {
        return <LoadingState />;
    }

    if (attachments.length === 0) {
        return <EmptyStateComponent />;
    }

    return <FileAttachmentList attachments={attachments} canEdit={false} fullWidth={true} />;
};

/**
 * Renders an application summary card for technical officers in the review queue.
 * Displays process metadata, application status, and reviewer workflow action buttons.
 * Notifies parent via callback when application status changes.
 */
export const ReviewCard = ({
    process,
    application,
    isHighlighted,
    onStatusChanged,
    onCardElementMounted,
}: {
    process: IAuthorisationProcess;
    application: IApplicationData;
    isHighlighted: boolean;
    onStatusChanged: (updatedApp: IApplicationData) => void;
    onCardElementMounted: (element: HTMLElement | null) => void;
}) => {
    const { showDialog, hideDialog } = useDialog();
    const { showSnackbar } = useSnackbar();

    const questionnaireName = `${application.questionnaire_name} (v${application.questionnaire_version})`;
    const statusCapitalised = formatStatusLabel(application.status);
    const { createdAtRelative, updatedAtRelative, submittedAtRelative } = formatRelativeDates(application);

    const handleFilesClick = () => {
        showDialog({
            title: `Attachments for #${application.internal_id}`,
            content: <AttachmentsDialogContent application={application} />,
        });
    };

    const handleEmailClick = () => {
        navigator.clipboard.writeText(application.owner_email)
            .then(() => {
                showSnackbar('Email address copied to clipboard', 'info');
            })
            .catch(() => {
                showSnackbar('Failed to copy email to clipboard', 'error');
            });
    };

    /**
     * Transition application from SUBMITTED to UNDER_REVIEW.
     * Reviewer claims the application for administrative review.
     */
    const handleClaim = async () => {
        let updatedApp: IApplicationData;
        try {
            updatedApp = await ApiManager.updateReviewerApplicationStatus(
                application.key,
                "UNDER_REVIEW" as ApplicationStatus,
            );
        } catch (error: unknown) {
            showSnackbar(
                "Failed to claim application. Please try again later.",
                "error",
            );
            console.error("Error claiming application:", error);
            return;
        }

        showSnackbar("Application claimed for review.", "success");
        onStatusChanged(updatedApp);
    };

    /**
     * Shows confirmation dialog for resetting application to draft.
     * Only proceeds with API call if user confirms the action.
     */
    const confirmResetToDraft = () => {
        showDialog({
            title: "Confirm reset to draft",
            content:
                <Box className="flex flex-col items-center justify-center px-4 gap-2">
                    <Typography sx={{ textAlign: "center" }}>
                        This will reset the application to <strong>"Draft"</strong> status,<br /> so the applicant can revise and resubmit.
                    </Typography>
                </Box>,
            actions: (
                <Button
                    variant="contained"
                    color="warning"
                    startIcon={<RestartAltRoundedIcon />}
                    onClick={async () => {
                        let updatedApp: IApplicationData;
                        try {
                            updatedApp = await ApiManager.updateReviewerApplicationStatus(
                                application.key,
                                "DRAFT" as ApplicationStatus,
                            );
                        } catch (error: unknown) {
                            showSnackbar(
                                "Failed to return application. Please try again later.",
                                "error",
                            );
                            console.error("Error returning application:", error);
                            hideDialog();
                            return;
                        }

                        showSnackbar("Application reset to draft for revision.", "info");
                        onStatusChanged(updatedApp);
                        // Close the dialog after action
                        hideDialog();
                    }}
                >
                    Confirm
                </Button>
            ),
        });
    };

    /**
     * Transition application from UNDER_REVIEW to UNDER_ASSESSMENT.
     * Escalates application to technical assessment after administrative checks pass.
     */
    const handleProceedtoAssessment = async () => {
        let updatedApp: IApplicationData;
        try {
            updatedApp = await ApiManager.updateReviewerApplicationStatus(
                application.key,
                "UNDER_ASSESSMENT" as ApplicationStatus,
            );
        } catch (error: unknown) {
            showSnackbar(
                "Failed to move application to assessment. Please try again later.",
                "error",
            );
            console.error("Error moving application to assessment:", error);
            hideDialog();
            return;
        }

        showSnackbar("Application moved to assessment.", "success");
        onStatusChanged(updatedApp);
        hideDialog();
    };

    /**
     * Shows confirmation dialog for proceeding application to assessment.
     * Only proceeds with API call if user confirms the action.
     */
    const confirmProceedToAssessment = () => {
        showDialog({
            title: "Confirm proceed to assessment",
            content:
                <Box className="flex flex-col items-center justify-center px-4 gap-2">
                    <Typography sx={{ textAlign: "center" }}>
                        This will move the application to "<strong>Under Assessment</strong>"<br /> status for decision-making.
                    </Typography>
                </Box>,
            actions: (
                <Button
                    variant="contained"
                    color="primary"
                    endIcon={<NavigateNextRoundedIcon />}
                    onClick={handleProceedtoAssessment}
                >
                    Confirm
                </Button>
            ),
        });
    };

    return (
        <ListItem className="mb-4">
            <Card 
                ref={(el) => onCardElementMounted(el as HTMLElement | null)}
                className={`p-8 w-full rounded-lg! ${isHighlighted ? 'card-highlight-blink' : ''}`}
                elevation={4}
            >
                {/* Header: Application ID on left, PDF/Files on right */}
                <Box className="flex justify-between items-start mb-4 gap-4">
                    <ApplicationIdDisplay internalId={application.internal_id} variant="h6" />
                    <Box className="flex gap-1">
                        <Tooltip title="View attachments" placement="top" arrow>
                            <IconButton
                                color="secondary"
                                size="large"
                                aria-label="View attachments"
                                onClick={handleFilesClick}
                            >
                                <AttachFileIcon />
                            </IconButton>
                        </Tooltip>
                        <Link
                            target="_blank"
                            rel="noopener"
                            aria-label="Download application PDF"
                            href={`/d/${application.key}`}
                        >
                            <Tooltip title="Download PDF" placement="top" arrow>
                                <IconButton
                                    color="primary"
                                    size="large"
                                    aria-label="Download PDF"
                                >
                                    <DownloadIcon />
                                </IconButton>
                            </Tooltip>
                        </Link>
                    </Box>
                </Box>

                <Box className="flex gap-2 my-4 flex-wrap justify-around">
                    <Chip label={process.name} size="small" variant="outlined" />
                    <Chip label={questionnaireName} size="small" variant="outlined" />

                    {/* Force a wrapped row break between identifier chips and status/date chips. */}
                    <Box className="basis-full h-0" />

                    <Chip label={`${statusCapitalised}`} size="small" variant="outlined" />
                    <Chip label={`Created ${createdAtRelative}`} size="small" variant="outlined" />
                    <Chip label={`Updated ${updatedAtRelative}`} size="small" variant="outlined" />
                </Box>

                <Box className="my-8 w-fit ml-16">
                    <Box className="flex flex-col gap-2">
                        {/* Applicant Name */}
                        <Box className="flex gap-1.5 items-center">
                            <PersonIcon fontSize="small" sx={{ color: 'action.active' }} />
                            <Typography variant="body2">
                                {application.owner_fullname || "Unknown applicant"}
                            </Typography>
                        </Box>

                        {/* Email - Clickable for copy to clipboard */}
                        <Tooltip title="Copy email address" placement="right" arrow>
                            <Box
                                className="flex gap-1.5 items-center cursor-pointer hover:opacity-70 transition-opacity duration-200 ease-in-out"
                                onClick={handleEmailClick}
                            >
                                <EmailIcon fontSize="small" sx={{ color: 'action.active' }} />
                                <Typography variant="body2" className="opacity-80">
                                    {application.owner_email}
                                </Typography>
                            </Box>
                        </Tooltip>

                        {/* Submission Date */}
                        <Box className="flex gap-1.5 items-center">
                            <HistoryIcon fontSize="small" sx={{ color: 'action.active' }} />
                            <Typography variant="body2">
                                Submitted {submittedAtRelative || "pending"}
                            </Typography>
                        </Box>
                    </Box>
                </Box>
                {/* Action buttons: left and right justified with space-between. */}
                <Box className="flex justify-between gap-1 mt-2">
                    {application.status === "SUBMITTED" && (
                        <Tooltip title="Claim application for review" placement="bottom" arrow>
                            <Button
                                className="ml-auto!"
                                variant="contained"
                                color="primary"
                                endIcon={<NavigateNextRoundedIcon />}
                                onClick={handleClaim}
                            >
                                Claim
                            </Button>
                        </Tooltip>
                    )}
                    {application.status === "UNDER_REVIEW" && (
                        <>
                            <Tooltip title="Reset application to draft for revision" placement="bottom" arrow>
                                <Button
                                    variant="contained"
                                    color="warning"
                                    startIcon={<RestartAltRoundedIcon />}
                                    onClick={confirmResetToDraft}
                                    className="w-32"
                                >
                                    Reset
                                </Button>
                            </Tooltip>
                            <Tooltip title="Coming soon..." placement="bottom" arrow>
                                <div>
                                    <Button
                                        disabled
                                        variant="contained"
                                        color="primary"
                                        startIcon={<ZoomInRoundedIcon />}
                                    >
                                        Review
                                    </Button>
                                </div>
                            </Tooltip>
                            <Tooltip title="Move application to assessment" placement="bottom" arrow>
                                <Button
                                    variant="contained"
                                    color="primary"
                                    endIcon={<NavigateNextRoundedIcon />}
                                    onClick={confirmProceedToAssessment}
                                    className="w-32"
                                >
                                    Assessment
                                </Button>
                            </Tooltip>
                        </>
                    )}
                </Box>
            </Card>
        </ListItem>
    );
};
