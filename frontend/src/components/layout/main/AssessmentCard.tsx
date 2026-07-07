import DownloadIcon from '@mui/icons-material/Download';
import SearchIcon from '@mui/icons-material/Search';
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
import type { IApplicationData } from "../../../context/types/Application";
import type { IAuthorisationProcess } from '../../../context/types/Questionnaire';
import { ApplicationIdDisplay } from '../../Common';
import {
    applicationSteps,
    downloadableStatuses,
    formatStatusLabel,
    formatRelativeDates,
    statusToActiveStep,
    terminatedStatuses,
} from './applicationCardUtils';

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
    const processName = process?.name ?? `Unknown process (${application.process_slug})`;
    const questionnaireName = `${application.questionnaire_name} (v${application.questionnaire_version})`;
    const statusCapitalised = formatStatusLabel(application.status);
    const { createdAtRelative, updatedAtRelative } = formatRelativeDates(application);

    const isTerminated = terminatedStatuses.has(application.status);
    const isDownloadable = downloadableStatuses.has(application.status);

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
                        aria-label="Review application"
                        onClick={() => openNewTab(`/a/${application.key}`, application.key)}
                    >
                        <Button
                            variant="contained"
                            color="info"
                            loadingPosition='start'
                            loading={false}
                            disabled={Boolean(false)}
                            startIcon={<SearchIcon />}
                        >
                            Review
                        </Button>
                    </Link>
                </Box>
            </Card>
        </ListItem>
    );
};
