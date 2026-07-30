import Box from "@mui/material/Box";
import List from "@mui/material/List";
import Tab from "@mui/material/Tab";
import Tabs from "@mui/material/Tabs";
import Typography from "@mui/material/Typography";

import { useEffect, useMemo, useState } from "react";
import { useLoaderData } from "react-router";
import { useResolvedPromise } from "../../../context/Hooks";
import { LocalStorage } from "../../../context/LocalStorage";
import type { IApplicationData } from "../../../context/types/Application";
import {
    activeStatuses,
    finalisedStatuses,
    terminatedStatuses,
} from '../../../context/types/Application';
import type { LoaderData } from '../../../context/types/Generic';
import { ApplicationCard } from "./ApplicationCard";
import { EmptyStateComponent } from "./EmptyState";
import { LoadingState } from "./LoadingState";
import {
    ApplicationSortControl,
    getAvailableSortOptions,
    getInitialSortOrder,
    sortApplications,
    type SortOrderOption,
} from './applicationUtils';

const myApplicationsSortOrderStorageKey = "my-applications-sort-order";

export const MyApplications = () => {
    const { processes, applications: applicationsPromise } = useLoaderData<LoaderData>();
    const [resolvedApplications, isApplicationsLoading] = useResolvedPromise<IApplicationData[]>(applicationsPromise, []);
    const [applicationUpdates, setApplicationUpdates] = useState<Record<string, IApplicationData>>({});
    const [selectedTab, setSelectedTab] = useState<number>(0);

    /**
     * Computes the merged applications list by overlaying any updates on the resolved applications.
     * This preserves the loading state while allowing real-time status changes to be reflected.
     */
    const applications = useMemo(
        () => resolvedApplications.map((app) => applicationUpdates[app.key] ?? app),
        [resolvedApplications, applicationUpdates],
    );

    const [sortOrder, setSortOrder] = useState<SortOrderOption>(() =>
        getInitialSortOrder(myApplicationsSortOrderStorageKey, "updated_newest")
    );

    useEffect(() => {
        LocalStorage.setValue<SortOrderOption>(myApplicationsSortOrderStorageKey, sortOrder);
    }, [sortOrder]);

    /**
     * Handles status changes from individual ApplicationCard components.
     * Records the update so re-categorisation and animations occur on the next render.
     */
    const handleApplicationStatusChanged = (updatedApp: IApplicationData) => {
        setApplicationUpdates((prev) => ({
            ...prev,
            [updatedApp.key]: updatedApp,
        }));
    };

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

    const categorisedApplications = useMemo(() => ({
        active: sortedApplications.filter((app) => activeStatuses.includes(app.status)),
        terminated: sortedApplications.filter((app) => terminatedStatuses.includes(app.status)),
        finalised: sortedApplications.filter((app) => finalisedStatuses.includes(app.status)),
    }), [sortedApplications]);

    const applicationsForTab = [
        categorisedApplications.active,
        categorisedApplications.terminated,
        categorisedApplications.finalised,
    ][selectedTab] || [];

    const tabDescriptions = [
        "View and manage your draft and submitted applications.",
        "View applications that have been discarded or withdrawn.",
        "View applications that have been approved, rejected, or deferred.",
    ];

    return (
        <Box className="p-8 w-full min-w-2xl lg:w-3xl xl:w-4xl">
            <Box className="flex justify-between items-center">
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
            <Box className="border-b border-gray-300 mb-4">
                <Tabs 
                    variant="fullWidth" 
                    value={selectedTab} 
                    onChange={(_, newValue) => setSelectedTab(newValue)}
                    aria-label="Application status filter"
                    role="tablist"
                >
                    <Tab 
                        label={`Active (${categorisedApplications.active.length})`} 
                        aria-label={`Active applications, ${categorisedApplications.active.length} total`}
                        id="tab-active"
                        aria-controls="tabpanel-active"
                        disabled={categorisedApplications.active.length === 0}
                    />
                    <Tab 
                        label={`Terminated (${categorisedApplications.terminated.length})`} 
                        aria-label={`Terminated applications, ${categorisedApplications.terminated.length} total`}
                        id="tab-terminated"
                        aria-controls="tabpanel-terminated"
                        disabled={categorisedApplications.terminated.length === 0}
                    />
                    <Tab 
                        label={`Finalised (${categorisedApplications.finalised.length})`} 
                        aria-label={`Finalised applications, ${categorisedApplications.finalised.length} total`}
                        id="tab-finalised"
                        aria-controls="tabpanel-finalised"
                        disabled={categorisedApplications.finalised.length === 0}
                    />
                </Tabs>
            </Box>

            <Typography color="textSecondary" className="mb-3!">
                {tabDescriptions[selectedTab]}
            </Typography>

            {isApplicationsLoading ? <LoadingState /> :
                applicationsForTab.length === 0 ? <EmptyStateComponent /> :
                    <List>
                        {applicationsForTab.map((a) => {
                            const process = processBySlug.get(a.process_slug);
                            return <ApplicationCard
                                key={a.key}
                                application={a}
                                process={process}
                                onStatusChanged={handleApplicationStatusChanged}
                            />;
                        })}
                    </List>
            }
        </Box>
    );
}