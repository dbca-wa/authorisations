import Box from "@mui/material/Box";
import List from "@mui/material/List";
import Tab from "@mui/material/Tab";
import Tabs from "@mui/material/Tabs";
import Typography from "@mui/material/Typography";

import { useEffect, useMemo, useRef, useState } from "react";
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
 * Organises applications into tabs by status: Submitted, Under Review, Under Assessment.
 * Applies reusable sorting controls and respects user preferences.
 */
export const ApplicationReview = () => {
    const { processes, applications: applicationsPromise } = useLoaderData<LoaderData>();
    const [resolvedApplications, isApplicationsLoading] = useResolvedPromise<IApplicationData[]>(applicationsPromise, []);
    const [applicationUpdates, setApplicationUpdates] = useState<Record<string, IApplicationData>>({});
    const [selectedTab, setSelectedTab] = useState<number>(0);
    const [highlightedAppKey, setHighlightedAppKey] = useState<string | null>(null);
    const cardRefsMap = useRef<Map<string, HTMLElement>>(new Map());

    /**
     * Computes the merged applications list by overlaying any updates on the resolved applications.
     * This preserves the loading state while allowing real-time status changes to be reflected.
     */
    const applications = useMemo(
        () => resolvedApplications.map((app) => applicationUpdates[app.key] ?? app),
        [resolvedApplications, applicationUpdates],
    );

    const [sortOrder, setSortOrder] = useState<SortOrderOption>(() =>
        getInitialSortOrder(reviewSortOrderStorageKey, "submitted_oldest")
    );

    useEffect(() => {
        LocalStorage.setValue<SortOrderOption>(reviewSortOrderStorageKey, sortOrder);
    }, [sortOrder]);

    /**
     * Handles status changes from individual ReviewCard components.
     * Records the update, switches to the appropriate tab, and highlights the changed application.
     */
    const handleApplicationStatusChanged = (updatedApp: IApplicationData) => {
        setApplicationUpdates((prev) => ({
            ...prev,
            [updatedApp.key]: updatedApp,
        }));

        // Switch to the tab matching the new status and highlight the application.
        const tabIndex = updatedApp.status === "SUBMITTED" ? 0 : updatedApp.status === "UNDER_REVIEW" ? 1 : 2;
        setSelectedTab(tabIndex);
        setHighlightedAppKey(updatedApp.key);

        // Clear highlight after animation completes.
        setTimeout(() => {
            setHighlightedAppKey(null);
        }, 3000);
    };

    /**
     * Registers a card element in the refs map for scroll-to-view targeting.
     */
    const handleCardElementMounted = (appKey: string, element: HTMLElement | null) => {
        if (element) {
            cardRefsMap.current.set(appKey, element);
        } else {
            cardRefsMap.current.delete(appKey);
        }
    };

    /**
     * Scrolls the highlighted card into view, centered on the screen.
     */
    useEffect(() => {
        if (highlightedAppKey) {
            const card = cardRefsMap.current.get(highlightedAppKey);
            if (card) {
                card.scrollIntoView({ behavior: "smooth", block: "center" });
            }
        }
    }, [highlightedAppKey]);

    const processBySlug = useMemo(
        () => new Map(processes.map((process) => [process.slug, process])),
        [processes]
    );

    const sortedReviewApplications = useMemo(
        () => sortApplications(applications, sortOrder),
        [applications, sortOrder]
    );

    /**
     * Groups applications by their review status into three categories.
     * Enables tab-based filtering for reviewers to navigate the review workflow.
     */
    const categorisedApplications = useMemo(() => ({
        submitted: sortedReviewApplications.filter((app) => app.status === "SUBMITTED"),
        underReview: sortedReviewApplications.filter((app) => app.status === "UNDER_REVIEW"),
        underAssessment: sortedReviewApplications.filter((app) => app.status === "UNDER_ASSESSMENT"),
    }), [sortedReviewApplications]);

    // Map tab index to the corresponding applications list for the selected tab.
    const applicationsForTab = [
        categorisedApplications.submitted,
        categorisedApplications.underReview,
        categorisedApplications.underAssessment,
    ][selectedTab] || [];

    const tabDescriptions = [
        "Claim submitted applications for administrative review.",
        "Perform administrative review and escalate to assessment.",
        "Finalise assessments and make approval decisions.",
    ];

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

            {/* Tab navigation for review queue statuses. */}
            <Box className="border-b border-gray-300 mb-4">
                <Tabs 
                    variant="fullWidth" 
                    value={selectedTab} 
                    onChange={(_, newValue) => setSelectedTab(newValue)}
                    aria-label="Application review status filter"
                    role="tablist"
                >
                    <Tab 
                        label={`Submitted (${categorisedApplications.submitted.length})`} 
                        aria-label={`Submitted applications, ${categorisedApplications.submitted.length} total`}
                        id="tab-submitted"
                        aria-controls="tabpanel-submitted"
                        disabled={categorisedApplications.submitted.length === 0}
                    />
                    <Tab 
                        label={`Under Review (${categorisedApplications.underReview.length})`} 
                        aria-label={`Under review applications, ${categorisedApplications.underReview.length} total`}
                        id="tab-under-review"
                        aria-controls="tabpanel-under-review"
                        disabled={categorisedApplications.underReview.length === 0}
                    />
                    <Tab 
                        label={`Under Assessment (${categorisedApplications.underAssessment.length})`} 
                        aria-label={`Under assessment applications, ${categorisedApplications.underAssessment.length} total`}
                        id="tab-under-assessment"
                        aria-controls="tabpanel-under-assessment"
                        disabled={categorisedApplications.underAssessment.length === 0}
                    />
                </Tabs>
            </Box>

            <Typography color="textSecondary" className="mb-3!">
                {tabDescriptions[selectedTab]}
            </Typography>

            {isApplicationsLoading ? <LoadingState /> :
                applicationsForTab.length === 0 ? <EmptyStateComponent /> :
                    <List>
                        {applicationsForTab.map((application) => {
                            const process = processBySlug.get(application.process_slug);
                            return <ReviewCard
                                key={application.key}
                                application={application}
                                process={process}
                                isHighlighted={application.key === highlightedAppKey}
                                onStatusChanged={handleApplicationStatusChanged}
                                onCardElementMounted={(el) => handleCardElementMounted(application.key, el)}
                            />;
                        })}
                    </List>
            }
        </Box>
    );
};
