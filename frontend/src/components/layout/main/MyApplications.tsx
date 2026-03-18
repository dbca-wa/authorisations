import NumbersIcon from '@mui/icons-material/Numbers';
import PlayArrowRoundedIcon from '@mui/icons-material/PlayArrowRounded';
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import Chip from "@mui/material/Chip";
import Link from '@mui/material/Link';
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import Step from "@mui/material/Step";
import StepLabel from "@mui/material/StepLabel";
import Stepper from "@mui/material/Stepper";
import Typography from "@mui/material/Typography";
import dayjs from 'dayjs';
import relativeTime from "dayjs/plugin/relativeTime";

import { useLoaderData } from "react-router";
import type { ApplicationStatus, IApplicationData } from "../../../context/types/Application";
import type { IAuthorisationProcess } from '../../../context/types/Questionnaire';
import { openNewTab } from '../../../context/Utils';
import { EmptyStateComponent } from "./EmptyState";

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

// Construct the application ID
const getApplicationId = (application: IApplicationData): string => {
    const questionnaireName = application.questionnaire_name.replace(/\s+/g, '-').toLowerCase();
    return `${application.process_slug}-${questionnaireName}-${application.id}`;
}


export const MyApplications = () => {
    const { processes, applications } = useLoaderData<{
        processes: IAuthorisationProcess[];
        applications: IApplicationData[];
    }>();
    const processBySlug = new Map(processes.map((process) => [process.slug, process]));

    return (
        <Box className="p-8 min-w-4xl max-w-7xl">
            <Typography variant="h4" gutterBottom>
                My Applications
            </Typography>
            <p>Here you can view and manage your applications.</p>

            {applications.length === 0 ? <EmptyStateComponent /> :
                <List>
                    {applications.map((a) => {
                        const process = processBySlug.get(a.process_slug);
                        return <Application key={a.key} application={a} process={process} />;
                    })}
                </List>
            }
        </Box>
    );
}

/** Display a MUI card for an application with action buttons; to resume or to download its certificate */
const Application = ({
    process,
    application,
}: {
    process?: IAuthorisationProcess;
    application: IApplicationData;
}) => {
    // Format dates
    dayjs.extend(relativeTime)
    const processName = process?.name ?? `Unknown process (${application.process_slug})`;
    const questionnaireName = `${application.questionnaire_name} (v${application.questionnaire_version})`;
    const statusCapitalised = application.status.split("_").map(s => s.charAt(0).toUpperCase() + s.slice(1).toLowerCase()).join(" ");
    const createdAtRelative = dayjs(application.created_at).fromNow()
    const updatedAtRelative = dayjs(application.updated_at).fromNow()

    return (
        <ListItem sx={{ marginBottom: 2 }}>
            <Card className="p-8 w-full" elevation={4} sx={{ borderRadius: 2 }}>
                <Typography variant="h6">
                    <NumbersIcon></NumbersIcon> {getApplicationId(application)}
                </Typography>

                <Box display="flex" gap={1} my={2} flexWrap="wrap" justifyContent={"center"}>
                    <Chip label={processName} size="small" variant="outlined" />
                    <Chip label={questionnaireName} size="small" variant="outlined" />
                    <Chip label={`${statusCapitalised}`} size="small" variant="outlined" />
                    <Chip label={`Created ${createdAtRelative}`} size="small" variant="outlined" />
                    <Chip label={`Updated ${updatedAtRelative}`} size="small" variant="outlined" />
                </Box>

                <Box mt={4} mb={1} className="w-4/5 mx-auto">
                    <Stepper activeStep={statusToActiveStep[application.status]} alternativeLabel>
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
    )
}