import NumbersIcon from '@mui/icons-material/Numbers';
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
    DISCARDED: 0,
    ACTION_REQUIRED: 0,
    SUBMITTED: 1,
    UNDER_REVIEW: 2,
    PROCESSING: 3,
    APPROVED: 4,
    REJECTED: 4,
};

/** Builds the human-readable application identifier shown on each card. */
const getApplicationId = (application: IApplicationData): string => {
    const questionnaireName = application.questionnaire_name.replace(/\s+/g, '-').toLowerCase();
    return `${application.process_slug}-${questionnaireName}-${application.id}`;
};

/**
 * Renders a reusable application summary card for both applicant and reviewer list pages.
 * It standardises status chips, timeline, and the continue action in one shared place.
 */
export const ApplicationCard = ({
    process,
    application,
}: {
    process?: IAuthorisationProcess;
    application: IApplicationData;
}) => {
    // Enable relative date labels like "2 days ago" for card metadata.
    dayjs.extend(relativeTime);

    const processName = process?.name ?? `Unknown process (${application.process_slug})`;
    const questionnaireName = `${application.questionnaire_name} (v${application.questionnaire_version})`;
    const statusCapitalised = application.status.split("_").map(s => s.charAt(0).toUpperCase() + s.slice(1).toLowerCase()).join(" ");
    const createdAtRelative = dayjs(application.created_at).fromNow();
    const updatedAtRelative = dayjs(application.updated_at).fromNow();

    return (
        <ListItem sx={{ marginBottom: 2 }}>
            <Card className="p-8 w-full" elevation={4} sx={{ borderRadius: 2 }}>
                <Typography variant="h6">
                    <NumbersIcon></NumbersIcon> {getApplicationId(application)}
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
                </Box>
                <Box display="flex" justifyContent="flex-end" mt={2}>
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