import Box from "@mui/material/Box";
import List from "@mui/material/List";
import Typography from "@mui/material/Typography";

import { useEffect, useMemo, useState } from "react";
import { useLoaderData } from "react-router";
import { useResolvedPromise } from "../../../context/Hooks";
import { LocalStorage } from "../../../context/LocalStorage";
import type { IApplicationData } from "../../../context/types/Application";
import type { LoaderData } from '../../../context/types/Generic';
import { LoadingState } from "./LoadingState";
import { ApplicationCard } from "./ApplicationCard";
import { EmptyStateComponent } from "./EmptyState";
import {
    ApplicationSortControl,
    getInitialSortOrder,
    getAvailableSortOptions,
    sortApplications,
    type SortOrderOption,
} from './applicationUtils';

const myApplicationsSortOrderStorageKey = "my-applications-sort-order";


export const MyApplications = () => {
    const { processes, applications: applicationsPromise } = useLoaderData<LoaderData>();
    const [applications, isApplicationsLoading] = useResolvedPromise<IApplicationData[]>(applicationsPromise, []);

    const [sortOrder, setSortOrder] = useState<SortOrderOption>(() =>
        getInitialSortOrder(myApplicationsSortOrderStorageKey, "updated_newest")
    );

    useEffect(() => {
        LocalStorage.setValue<SortOrderOption>(myApplicationsSortOrderStorageKey, sortOrder);
    }, [sortOrder]);

    const processBySlug = useMemo(
        () => new Map(processes.map((process) => [process.slug, process])),
        [processes]
    );

    // Remove `applications` content for empty state testing
    // applications.length = 0;

    const sortedApplications = useMemo(
        () => sortApplications(applications, sortOrder),
        [applications, sortOrder]
    );

    return (
        <Box className="p-8 w-full min-w-2xl lg:w-3xl xl:w-4xl">
            <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <Typography variant="h4" gutterBottom>
                    My Applications
                </Typography>
                {!isApplicationsLoading && applications.length > 1 &&
                    <ApplicationSortControl
                        value={sortOrder}
                        onChange={setSortOrder}
                        controlId="my-applications-sort"
                        availableOptions={getAvailableSortOptions(applications)}
                    />
                }
            </Box>
            <Typography color="textSecondary" sx={{ mb: 4 }}>
                View and manage your submitted and draft applications.
            </Typography>

            {isApplicationsLoading ? <LoadingState /> :
                applications.length === 0 ? <EmptyStateComponent /> :
                    <List>
                        {sortedApplications.map((a) => {
                            const process = processBySlug.get(a.process_slug);
                            return <ApplicationCard
                                key={a.key}
                                application={a}
                                process={process}
                            />;
                        })}
                    </List>
            }
        </Box>
    );
}