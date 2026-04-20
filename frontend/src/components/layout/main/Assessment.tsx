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

const assessmentRelevantStatuses = ["SUBMITTED", "UNDER_REVIEW", "ACTION_REQUIRED", "UNDER_ASSESSMENT"] as const;

/**
 * Displays applications in the assessment queue for technical officers.
 * This page resolves deferred loader data and prioritises active assessment statuses.
 */
export const ApplicationAssessment = () => {
    const { processes, applications: applicationsPromise } = useLoaderData<LoaderData>();
    const [applications, isApplicationsLoading] = useResolvedPromise<IApplicationData[]>(applicationsPromise, []);

    const processBySlug = useMemo(
        () => new Map(processes.map((process) => [process.slug, process])),
        [processes]
    );

    /**
     * Orders the assessment queue with actively progressing statuses first, then most recently updated.
     * This helps technical officers focus on currently actionable work.
     */
    const sortedAssessmentApplications = useMemo(() => {
        const assessmentStatusRank = new Map(assessmentRelevantStatuses.map((status, index) => [status, index]));

        return [...applications].sort((a, b) => {
            const statusRankA = assessmentStatusRank.get(a.status as (typeof assessmentRelevantStatuses)[number]) ?? Number.MAX_SAFE_INTEGER;
            const statusRankB = assessmentStatusRank.get(b.status as (typeof assessmentRelevantStatuses)[number]) ?? Number.MAX_SAFE_INTEGER;

            // First sort by assessment workflow priority.
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
                Application Assessment 
            </Typography>
            <p>Here you can assess and action applications assigned to your assessment stream.</p>

            {isApplicationsLoading ? <Typography>Loading applications...</Typography> :
                sortedAssessmentApplications.length === 0 ? <EmptyStateComponent /> :
                    <List>
                        {sortedAssessmentApplications.map((application) => {
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
