import AttachFileIcon from '@mui/icons-material/AttachFile';
import DownloadIcon from '@mui/icons-material/Download';
import EmailIcon from '@mui/icons-material/Email';
import HistoryIcon from '@mui/icons-material/History';
import PersonIcon from '@mui/icons-material/Person';
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import Chip from "@mui/material/Chip";
import Typography from "@mui/material/Typography";
import Link from '@mui/material/Link';
import ListItem from "@mui/material/ListItem";

import { useState } from 'react';
import { ApiManager } from '../../../context/ApiManager';
import { useDialog, useResolvedPromise, useSnackbar } from '../../../context/Hooks';
import type { IApplicationAttachment, IApplicationData } from "../../../context/types/Application";
import type { IAuthorisationProcess } from '../../../context/types/Questionnaire';
import { ApplicationIdDisplay, FileAttachmentList } from '../../Common';
import {
    downloadableStatuses,
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
 * Renders an application summary card for technical officers in the assessment queue.
 * Displays process metadata, application status, and review/download action buttons.
 */
export const AssessmentCard = ({
    process,
    application,
}: {
    process?: IAuthorisationProcess;
    application: IApplicationData;
}) => {
    const { showDialog } = useDialog();
    const { showSnackbar } = useSnackbar();

    const processName = process?.name ?? `Unknown process (${application.process_slug})`;
    const questionnaireName = `${application.questionnaire_name} (v${application.questionnaire_version})`;
    const statusCapitalised = formatStatusLabel(application.status);
    const { createdAtRelative, updatedAtRelative } = formatRelativeDates(application);

    const isDownloadable = downloadableStatuses.has(application.status);

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
                        <Box
                            className="flex gap-1.5 items-center cursor-pointer hover:opacity-70 transition-opacity duration-200 ease-in-out"
                            onClick={handleEmailClick}
                            title="Click to copy email address"
                        >
                            <EmailIcon fontSize="small" sx={{ color: 'action.active' }} />
                            <Typography variant="body2" className="opacity-80">
                                {application.owner_email}
                            </Typography>
                        </Box>

                        {/* Submission Date */}
                        <Box className="flex gap-1.5 items-center">
                            <HistoryIcon fontSize="small" sx={{ color: 'action.active' }} />
                            <Typography variant="body2">
                                Submitted {createdAtRelative}
                            </Typography>
                        </Box>
                    </Box>
                </Box>
                <Box className="flex justify-end gap-1 mt-2">
                    <Button
                        variant="outlined"
                        color="secondary"
                        loadingPosition='start'
                        loading={false}
                        disabled={false}
                        startIcon={<AttachFileIcon />}
                        onClick={handleFilesClick}
                    >
                        Files
                    </Button>

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
                                PDF
                            </Button>
                        </Link>
                    )}
                </Box>
            </Card>
        </ListItem>
    );
};
