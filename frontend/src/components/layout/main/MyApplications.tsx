import SortIcon from '@mui/icons-material/Sort';
import Box from "@mui/material/Box";
import FormControl from "@mui/material/FormControl";
import List from "@mui/material/List";
import MenuItem from "@mui/material/MenuItem";
import Select from "@mui/material/Select";
import Typography from "@mui/material/Typography";

import { useEffect, useMemo, useState } from "react";
import { useLoaderData } from "react-router";
import { useResolvedPromise } from "../../../context/Hooks";
import { LocalStorage } from "../../../context/LocalStorage";
import type { ApplicationStatus, IApplicationData } from "../../../context/types/Application";
import type { LoaderData } from '../../../context/types/Generic';
import { ApplicationCard } from "./ApplicationCard";
import { EmptyStateComponent } from "./EmptyState";

const sortOrderOptions = [
    "authorisation",
    "newest",
    "oldest",
    "recently_updated",
    "least_recently_updated",
] as const;

type SortOrderOption = typeof sortOrderOptions[number];

const myApplicationsSortOrderStorageKey = "my-applications-sort-order";
const defaultSortOrder: SortOrderOption = "newest";

const isSortOrderOption = (value: string): value is SortOrderOption => {
    return sortOrderOptions.includes(value as SortOrderOption);
};

const getInitialSortOrder = (): SortOrderOption => {
    const storedValue = LocalStorage.getValue<string>(myApplicationsSortOrderStorageKey);
    if (storedValue && isSortOrderOption(storedValue)) {
        return storedValue;
    }

    return defaultSortOrder;
};

const sortOrderLabels: Record<SortOrderOption, string> = {
    authorisation: "Authorisation",
    newest: "Newest",
    oldest: "Oldest",
    recently_updated: "Recently updated",
    least_recently_updated: "Least recently updated",
};

/** Statuses that the download link should be visible. */
const downloadableStatuses = new Set<ApplicationStatus>([
    "SUBMITTED",
    "UNDER_REVIEW",
    "UNDER_ASSESSMENT",
    "APPROVED",
    "APPROVED_WITH_CONDITIONS",
    "DEFERRED",
    "REJECTED"
]);


export const MyApplications = () => {
    const { processes, applications: applicationsPromise } = useLoaderData<LoaderData>();
    const [applications, isApplicationsLoading] = useResolvedPromise<IApplicationData[]>(applicationsPromise, []);

    // Default to newest and restore the user's last selected sort when available.
    const [sortOrder, setSortOrder] = useState<SortOrderOption>(getInitialSortOrder);

    useEffect(() => {
        LocalStorage.setValue<SortOrderOption>(myApplicationsSortOrderStorageKey, sortOrder);
    }, [sortOrder]);

    const processBySlug = useMemo(
        () => new Map(processes.map((process) => [process.slug, process])),
        [processes]
    );

    // Remove `applications` content for empty state testing
    // applications.length = 0;

    const sortedApplications = useMemo(() => {
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
            <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2 }}>
                <Typography variant="h4" gutterBottom>
                    My Applications
                </Typography>
                {!isApplicationsLoading && applications.length > 0 &&
                    <FormControl size="small">
                        <Select
                            id="my-applications-sort"
                            value={sortOrder}
                            className="min-w-55"
                            displayEmpty
                            onChange={(event) => setSortOrder(event.target.value as SortOrderOption)}
                            inputProps={{ 'aria-label': 'Sort applications' }}
                            renderValue={(selected) => {
                                const option = selected as SortOrderOption;

                                return (
                                    <Box
                                        component="span"
                                        sx={{ display: "inline-flex", alignItems: "center", gap: 1 }}
                                    >
                                        <SortIcon fontSize="small" />
                                        <Box component="span">{sortOrderLabels[option]}</Box>
                                    </Box>
                                );
                            }}
                        >
                            {sortOrderOptions.map((option) => (
                                <MenuItem key={option} value={option}>
                                    {sortOrderLabels[option]}
                                </MenuItem>
                            ))}
                        </Select>
                    </FormControl>
                }
            </Box>
            <p>Here you can view and manage your applications.</p>

            {isApplicationsLoading ? <Typography>Loading applications...</Typography> :
                applications.length === 0 ? <EmptyStateComponent /> :
                    <List>
                        {sortedApplications.map((a) => {
                            const process = processBySlug.get(a.process_slug);
                            const downloadUrl = downloadableStatuses.has(a.status) ? `/d/${a.key}` : undefined;
                            return <ApplicationCard
                                key={a.key}
                                application={a}
                                process={process}
                                downloadUrl={downloadUrl}
                                displayContinue={true}
                            />;
                        })}
                    </List>
            }
        </Box>
    );
}