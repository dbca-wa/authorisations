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
import { AssessmentCard } from "./AssessmentCard";
import { EmptyStateComponent } from "./EmptyState";
import {
    ApplicationSortControl,
    getInitialSortOrder,
    sortApplications,
    type SortOrderOption,
} from './applicationUtils';

const assessmentSortOrderStorageKey = "assessment-sort-order";

/**
 * Displays applications in the assessment queue for technical officers.
 * Applies reusable sorting controls and respects user preferences.
 */
export const ApplicationAssessment = () => {
    const { processes, applications: applicationsPromise } = useLoaderData<LoaderData>();
    const [applications, isApplicationsLoading] = useResolvedPromise<IApplicationData[]>(applicationsPromise, []);

    const [sortOrder, setSortOrder] = useState<SortOrderOption>(() =>
        getInitialSortOrder(assessmentSortOrderStorageKey)
    );

    useEffect(() => {
        LocalStorage.setValue<SortOrderOption>(assessmentSortOrderStorageKey, sortOrder);
    }, [sortOrder]);

    const processBySlug = useMemo(
        () => new Map(processes.map((process) => [process.slug, process])),
        [processes]
    );

    const sortedAssessmentApplications = useMemo(
        () => sortApplications(applications, sortOrder, processBySlug),
        [applications, sortOrder, processBySlug]
    );

    return (
        <Box className="p-8 w-full min-w-2xl lg:w-3xl xl:w-4xl">
            <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <Typography variant="h4" gutterBottom>
                    Application Assessment
                </Typography>
                {!isApplicationsLoading && sortedAssessmentApplications.length > 1 &&
                    <ApplicationSortControl
                        value={sortOrder}
                        onChange={setSortOrder}
                        controlId="assessment-sort"
                    />
                }
            </Box>
            <Typography color="textSecondary" sx={{ mb: 4 }}>
                Assess and action applications in your queue.
            </Typography>

            {isApplicationsLoading ? <LoadingState /> :
                sortedAssessmentApplications.length === 0 ? <EmptyStateComponent /> :
                    <List>
                        {sortedAssessmentApplications.map((application) => {
                            const process = processBySlug.get(application.process_slug);
                            return <AssessmentCard
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
