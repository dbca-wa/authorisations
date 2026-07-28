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
import { ReviewCard } from "./ReviewCard";
import { EmptyStateComponent } from "./EmptyState";
import {
    ApplicationSortControl,
    getInitialSortOrder,
    getAvailableSortOptions,
    sortApplications,
    type SortOrderOption,
} from './applicationUtils';

const reviewSortOrderStorageKey = "review-sort-order";

/**
 * Displays applications in the review queue for technical officers.
 * Applies reusable sorting controls and respects user preferences.
 */
export const ApplicationReview = () => {
    const { processes, applications: applicationsPromise } = useLoaderData<LoaderData>();
    const [applications, isApplicationsLoading] = useResolvedPromise<IApplicationData[]>(applicationsPromise, []);

    const [sortOrder, setSortOrder] = useState<SortOrderOption>(() =>
        getInitialSortOrder(reviewSortOrderStorageKey, "submitted_oldest")
    );

    useEffect(() => {
        LocalStorage.setValue<SortOrderOption>(reviewSortOrderStorageKey, sortOrder);
    }, [sortOrder]);

    const processBySlug = useMemo(
        () => new Map(processes.map((process) => [process.slug, process])),
        [processes]
    );

    const sortedReviewApplications = useMemo(
        () => sortApplications(applications, sortOrder),
        [applications, sortOrder]
    );

    return (
        <Box className="p-8 w-full min-w-2xl lg:w-3xl xl:w-4xl">
            <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <Typography variant="h4" gutterBottom>
                    Application Review
                </Typography>
                {!isApplicationsLoading && sortedReviewApplications.length > 1 &&
                    <ApplicationSortControl
                        value={sortOrder}
                        onChange={setSortOrder}
                        controlId="review-sort"
                        availableOptions={getAvailableSortOptions(applications)}
                    />
                }
            </Box>
            <Typography color="textSecondary" sx={{ mb: 4 }}>
                Review and action applications in your queue.
            </Typography>

            {isApplicationsLoading ? <LoadingState /> :
                sortedReviewApplications.length === 0 ? <EmptyStateComponent /> :
                    <List>
                        {sortedReviewApplications.map((application) => {
                            const process = processBySlug.get(application.process_slug);
                            return <ReviewCard
                                key={application.key}
                                application={application}
                                process={process}
                            />;
                        })}
                    </List>
            }
        </Box>
    );
};
