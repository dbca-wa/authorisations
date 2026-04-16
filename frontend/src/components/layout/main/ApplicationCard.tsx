import NumbersIcon from '@mui/icons-material/Numbers';
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
import Typography from "@mui/material/Typography";
import dayjs from 'dayjs';
import relativeTime from "dayjs/plugin/relativeTime";

import type { ApplicationStatus, IApplicationData } from "../../../context/types/Application";
import type { IAuthorisationProcess } from '../../../context/types/Questionnaire';
import { openNewTab } from '../../../context/Utils';

const applicationSteps = [
    "Application",
    "Submit",
    "Review",
    "Assessment",
    "Decision",
] as const;

const statusToActiveStep: Record<ApplicationStatus, number> = {
    DRAFT: 0,
    DISCARDED: 0,           // Terminated during drafting — never submitted.
    ACTION_REQUIRED: 0,
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
 * Renders a reusable application summary card for both applicant and reviewer list pages.
 * It standardises status chips, timeline, and the continue action in one shared place.
 */
export const ApplicationCard = ({
    process,
    application,
    downloadUrl,
}: {
    process?: IAuthorisationProcess;
    application: IApplicationData;
    downloadUrl?: string;
}) => {
    // Enable relative date labels like "2 days ago" for card metadata.
    dayjs.extend(relativeTime);

    const processName = process?.name ?? `Unknown process (${application.process_slug})`;
    const questionnaireName = `${application.questionnaire_name} (v${application.questionnaire_version})`;
    const statusCapitalised = application.status.split("_").map(s => s.charAt(0).toUpperCase() + s.slice(1).toLowerCase()).join(" ");
    const createdAtRelative = dayjs(application.created_at).fromNow();
    const updatedAtRelative = dayjs(application.updated_at).fromNow();

    const isTerminated = terminatedStatuses.has(application.status);

    return (
        <ListItem sx={{ marginBottom: 2 }}>
            <Card className="p-8 w-full" elevation={4} sx={{ borderRadius: 2 }}>
                <Typography variant="h6">
                    <NumbersIcon></NumbersIcon>{application.internal_id}
                </Typography>

                <Box display="flex" gap={1} my={2} flexWrap="wrap" justifyContent="space-around" className="max-w-min min-w-1/1 mx-auto">
                    <Chip label={processName} size="small" variant="outlined" />
                    <Chip label={questionnaireName} size="small" variant="outlined" />

                    {/* Force a wrapped row break between identifier chips and status/date chips. */}
                    <Box sx={{ flexBasis: "100%", height: 0 }} />

                    <Chip label={`${statusCapitalised}`} size="small" variant="outlined" />
                    <Chip label={`Created ${createdAtRelative}`} size="small" variant="outlined" />
                    <Chip label={`Updated ${updatedAtRelative}`} size="small" variant="outlined" />
                </Box>

                <Box mt={4} mb={1} className="w-4/5 mx-auto">
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
                <Box display="flex" justifyContent="flex-end" gap={1} mt={2}>
                    {/* Render the PDF action only when explicitly enabled and a designated URL is provided. */}
                    {downloadUrl && (
                        <Link
                            target="_blank"
                            rel="noopener"
                            aria-label="Download application PDF"
                            href={downloadUrl}
                        >
                            <Button
                                variant="outlined"
                                color="primary"
                                loadingPosition='start'
                                loading={false}
                                disabled={Boolean(false)}
                                startIcon={<DownloadIcon />}
                            >
                                Download
                            </Button>
                        </Link>
                    )}

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
                            disabled={Boolean(false)}
                            startIcon={<PlayArrowRoundedIcon />}
                        >
                            Continue
                        </Button>
                    </Link>
                </Box>
            </Card>
        </ListItem>
    );
};