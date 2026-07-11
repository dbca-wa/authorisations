import AttachFileIcon from '@mui/icons-material/AttachFile';
import DownloadIcon from '@mui/icons-material/Download';
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import Chip from "@mui/material/Chip";
import Link from '@mui/material/Link';
import ListItem from "@mui/material/ListItem";
import Step from "@mui/material/Step";
import StepLabel from "@mui/material/StepLabel";
import Stepper from "@mui/material/Stepper";

import { useState } from 'react';
import { ApiManager } from '../../../context/ApiManager';
import { useDialog, useResolvedPromise } from '../../../context/Hooks';
import type { IApplicationAttachment, IApplicationData } from "../../../context/types/Application";
import type { IAuthorisationProcess } from '../../../context/types/Questionnaire';
import { ApplicationIdDisplay, FileAttachmentList } from '../../Common';
import {
    applicationSteps,
    downloadableStatuses,
    formatRelativeDates,
    formatStatusLabel,
    statusToActiveStep,
    terminatedStatuses,
} from './applicationCardUtils';
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

    return <FileAttachmentList attachments={attachments} canEdit={false} />;
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

    const processName = process?.name ?? `Unknown process (${application.process_slug})`;
    const questionnaireName = `${application.questionnaire_name} (v${application.questionnaire_version})`;
    const statusCapitalised = formatStatusLabel(application.status);
    const { createdAtRelative, updatedAtRelative } = formatRelativeDates(application);

    const isTerminated = terminatedStatuses.has(application.status);
    const isDownloadable = downloadableStatuses.has(application.status);

    const handleFilesClick = () => {
        showDialog({
            title: `Attachments for #${application.internal_id}`,
            content: <AttachmentsDialogContent application={application} />,
        });
    };

    return (
        <ListItem sx={{ marginBottom: 2 }}>
            <Card className="p-8 w-full" elevation={4} sx={{ borderRadius: 2 }}>
                <ApplicationIdDisplay internalId={application.internal_id} variant="h6" />

                <Box sx={{ display: "flex", gap: 1, my: 2, flexWrap: "wrap", justifyContent: "space-around" }} className="max-w-min min-w-1/1 mx-auto">
                    <Chip label={processName} size="small" variant="outlined" />
                    <Chip label={questionnaireName} size="small" variant="outlined" />

                    {/* Force a wrapped row break between identifier chips and status/date chips. */}
                    <Box sx={{ flexBasis: "100%", height: 0 }} />

                    <Chip label={`${statusCapitalised}`} size="small" variant="outlined" />
                    <Chip label={`Created ${createdAtRelative}`} size="small" variant="outlined" />
                    <Chip label={`Updated ${updatedAtRelative}`} size="small" variant="outlined" />
                </Box>

                <Box sx={{ mt: 4, mb: 1 }} className="w-4/5 mx-auto">
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
                <Box sx={{ display: "flex", justifyContent: "flex-end", gap: 1, mt: 2 }}>
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
