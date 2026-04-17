import Box from "@mui/material/Box";
import List from "@mui/material/List";
import Typography from "@mui/material/Typography";

import { useMemo } from "react";
import { useLoaderData } from "react-router";
import type { IApplicationData } from "../../../context/types/Application";
import type { LoaderData } from '../../../context/types/Generic';
import { useResolvedPromise } from "../../Common";
import { ApplicationCard } from "./ApplicationCard";
import { EmptyStateComponent } from "./EmptyState";

const reviewRelevantStatuses = ["SUBMITTED", "UNDER_REVIEW", "ACTION_REQUIRED", "UNDER_ASSESSMENT"] as const;

/**
 * Displays applications for technical officer review workflows.
 * This page resolves deferred loader data and prioritises active review statuses.
 */
export const ReviewApplications = () => {
    const { processes, applications: applicationsPromise } = useLoaderData<LoaderData>();
    const [applications, isApplicationsLoading] = useResolvedPromise<IApplicationData[]>(applicationsPromise, []);

    const processBySlug = useMemo(
        () => new Map(processes.map((process) => [process.slug, process])),
        [processes]
    );

    /**
     * Orders review list with actively reviewed statuses first, then most recently updated.
     * This helps technical officers focus on currently actionable work.
     */
    const sortedReviewApplications = useMemo(() => {
        const reviewStatusRank = new Map(reviewRelevantStatuses.map((status, index) => [status, index]));

        return [...applications].sort((a, b) => {
            const statusRankA = reviewStatusRank.get(a.status as (typeof reviewRelevantStatuses)[number]) ?? Number.MAX_SAFE_INTEGER;
            const statusRankB = reviewStatusRank.get(b.status as (typeof reviewRelevantStatuses)[number]) ?? Number.MAX_SAFE_INTEGER;

            // First sort by review workflow priority.
            if (statusRankA !== statusRankB) {
                return statusRankA - statusRankB;
            }

            // Then sort by freshest activity within each status bucket.
            return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
        });
    }, [applications]);

    return (
        <Box className="p-8 min-w-4xl max-w-7xl">
            <Typography variant="h4" gutterBottom>
                Review Applications
            </Typography>
            <p>Here you can review and action applications assigned to your review stream.</p>

            {isApplicationsLoading ? <Typography>Loading applications...</Typography> :
                sortedReviewApplications.length === 0 ? <EmptyStateComponent /> :
                    <List>
                        {sortedReviewApplications.map((application) => {
                            const process = processBySlug.get(application.process_slug);
                            return <ApplicationCard
                                key={application.key}
                                application={application}
                                process={process}
                                downloadUrl={`/d/${application.key}`}
                            />;
                        })}
                    </List>
            }
        </Box>
    );
};
