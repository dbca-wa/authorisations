import NumbersIcon from '@mui/icons-material/Numbers';
import PlayArrowRoundedIcon from '@mui/icons-material/PlayArrowRounded';
import SortIcon from '@mui/icons-material/Sort';
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import Chip from "@mui/material/Chip";
import FormControl from "@mui/material/FormControl";
import Link from '@mui/material/Link';
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import MenuItem from "@mui/material/MenuItem";
import Select from "@mui/material/Select";
import Step from "@mui/material/Step";
import StepLabel from "@mui/material/StepLabel";
import Stepper from "@mui/material/Stepper";
import Typography from "@mui/material/Typography";
import dayjs from 'dayjs';
import relativeTime from "dayjs/plugin/relativeTime";
import { useMemo, useState } from "react";

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

type SortOrderOption =
    | "none"
    | "authorisation"
    | "newest"
    | "oldest"
    | "recently_updated"
    | "least_recently_updated";

const sortOrderLabels: Record<SortOrderOption, string> = {
    none: "Sort by",
    authorisation: "Authorisation",
    newest: "Newest",
    oldest: "Oldest",
    recently_updated: "Recently updated",
    least_recently_updated: "Least recently updated",
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
    const [sortOrder, setSortOrder] = useState<SortOrderOption>("none");

    const processBySlug = useMemo(
        () => new Map(processes.map((process) => [process.slug, process])),
        [processes]
    );

    // Remove `applications` content for empty state testing
    // applications.length = 0;

    const sortedApplications = useMemo(() => {
        if (sortOrder === "none") {
            // Preserve the original loader order when no sort is selected.
            return applications;
        }

        const sorted = [...applications];

        if (sortOrder === "authorisation") {
            // Group by process display order, then by slug for stable ordering.
            sorted.sort((a, b) => {
                const processA = processBySlug.get(a.process_slug);
                const processB = processBySlug.get(b.process_slug);
                const processOrderA = processA?.sort_order ?? Number.MAX_SAFE_INTEGER;
                const processOrderB = processB?.sort_order ?? Number.MAX_SAFE_INTEGER;

                // If the two applications belong to processes with different display orders,
                // use that configured process ordering first.
                if (processOrderA !== processOrderB) {
                    return processOrderA - processOrderB;
                }

                // When both processes resolve to the same sort order, fall back to slug text
                // so the result stays deterministic and does not jump around between renders.
                return a.process_slug.localeCompare(b.process_slug);
            });
            return sorted;
        }

        if (sortOrder === "newest") {
            // Show the most recently created applications first.
            sorted.sort(
                (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
            );
            return sorted;
        }

        if (sortOrder === "oldest") {
            // Show the earliest created applications first.
            sorted.sort(
                (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
            );
            return sorted;
        }

        if (sortOrder === "recently_updated") {
            // Prioritise applications with the latest activity.
            sorted.sort(
                (a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
            );
            return sorted;
        }

        // Surface applications with the oldest updates first.
        sorted.sort(
            (a, b) => new Date(a.updated_at).getTime() - new Date(b.updated_at).getTime()
        );
        return sorted;
    }, [applications, processBySlug, sortOrder]);

    return (
        <Box className="p-8 min-w-4xl max-w-7xl">
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h4" gutterBottom>
                    My Applications
                </Typography>
                {applications.length > 0 &&
                    <FormControl size="small">
                        <Select
                            id="my-applications-sort"
                            value={sortOrder}
                            className="min-w-[220px]"
                            displayEmpty
                            onChange={(event) => setSortOrder(event.target.value as SortOrderOption)}
                            inputProps={{ 'aria-label': 'Sort applications' }}
                            renderValue={(selected) => {
                                const option = selected as SortOrderOption;
                                const isPlaceholder = option === "none";

                                return (
                                    <Box
                                        component="span"
                                        display="inline-flex"
                                        alignItems="center"
                                        gap={1}
                                        sx={{ color: isPlaceholder ? 'text.secondary' : 'text.primary' }}
                                    >
                                        <SortIcon fontSize="small" />
                                        <Box component="span">{sortOrderLabels[option]}</Box>
                                    </Box>
                                );
                            }}
                        >
                            <MenuItem value="none" sx={{ color: 'text.secondary', fontStyle: 'italic' }}>
                                Sort by
                            </MenuItem>
                            <MenuItem value="authorisation">Authorisation</MenuItem>
                            <MenuItem value="newest">Newest</MenuItem>
                            <MenuItem value="oldest">Oldest</MenuItem>
                            <MenuItem value="recently_updated">Recently updated</MenuItem>
                            <MenuItem value="least_recently_updated">Least recently updated</MenuItem>
                        </Select>
                    </FormControl>
                }
            </Box>
            <p>Here you can view and manage your applications.</p>

            {applications.length === 0 ? <EmptyStateComponent /> :
                <List>
                    {sortedApplications.map((a) => {
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