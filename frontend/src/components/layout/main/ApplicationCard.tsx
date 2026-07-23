import DownloadIcon from '@mui/icons-material/Download';
import PlayArrowRoundedIcon from '@mui/icons-material/PlayArrowRounded';
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import Chip from "@mui/material/Chip";
import Link from '@mui/material/Link';
import ListItem from "@mui/material/ListItem";
import Step from "@mui/material/Step";
import StepLabel from "@mui/material/StepLabel";
import Stepper from "@mui/material/Stepper";

import { openNewTab } from '../../../context/Utils';
import type { ApplicationStatus, IApplicationData } from "../../../context/types/Application";
import type { IAuthorisationProcess } from '../../../context/types/Questionnaire';
import { ApplicationIdDisplay } from '../../Common';
import {
    downloadableStatuses,
    formatStatusLabel,
    formatRelativeDates,
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
 */
export const ApplicationCard = ({
    process,
    application,
}: {
    process?: IAuthorisationProcess;
    application: IApplicationData;
}) => {
    const processName = process?.name ?? `Unknown process (${application.process_slug})`;
    const questionnaireName = `${application.questionnaire_name} (v${application.questionnaire_version})`;
    const statusCapitalised = formatStatusLabel(application.status);
    const { createdAtRelative, updatedAtRelative } = formatRelativeDates(application);

    const isTerminated = terminatedStatuses.has(application.status);
    const isDownloadable = downloadableStatuses.has(application.status);
    const isEditable = application.status === "DRAFT";

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
                <Box className="flex justify-end gap-1 mt-2">
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
            </Card>
        </ListItem>
    );
};