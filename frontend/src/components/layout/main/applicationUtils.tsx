/* eslint-disable react-refresh/only-export-components */
import SortIcon from '@mui/icons-material/Sort';
import Box from "@mui/material/Box";
import FormControl from "@mui/material/FormControl";
import MenuItem from "@mui/material/MenuItem";
import Select from "@mui/material/Select";
import _ from "underscore";
import dayjs from "dayjs";
import relativeTime from "dayjs/plugin/relativeTime";

import { LocalStorage } from "../../../context/LocalStorage";
import type { ApplicationStatus, IApplicationData } from "../../../context/types/Application";

// Enable relative date labels like "2 days ago" for card metadata.
dayjs.extend(relativeTime);

// ============================================================================
// Shared Utilities (used by multiple components: ApplicationCard, AssessmentCard)
// ============================================================================

/**
 * Formats a status string into title-cased display text.
 * Example: "UNDER_REVIEW" → "Under Review"
 */
export const formatStatusLabel = (status: ApplicationStatus): string => {
    return status
        .split("_")
        .map(s => s.charAt(0).toUpperCase() + s.slice(1).toLowerCase())
        .join(" ");
};

/**
 * Formats application metadata dates into relative format.
 * Returns strings like "2 days ago", "just now", etc.
 * Returns null for submittedAtRelative if the application hasn't been submitted.
 */
export const formatRelativeDates = (application: IApplicationData) => {
    return {
        createdAtRelative: dayjs(application.created_at).fromNow(),
        updatedAtRelative: dayjs(application.updated_at).fromNow(),
        submittedAtRelative: application.submitted_at ? dayjs(application.submitted_at).fromNow() : null,
    };
};

/** Statuses for which a download link should be available. */
export const downloadableStatuses = new Set<ApplicationStatus>([
    "SUBMITTED",
    "UNDER_REVIEW",
    "UNDER_ASSESSMENT",
    "APPROVED",
    "APPROVED_WITH_CONDITIONS",
    "DEFERRED",
    "REJECTED"
]);

// ============================================================================
// Application Sorting (reusable across pages)
// ============================================================================

export const sortOrderOptions = [
    "application_type",
    "submitted_newest",
    "submitted_oldest",
    "created_newest",
    "created_oldest",
    "updated_newest",
    "updated_oldest",
] as const;

export type SortOrderOption = typeof sortOrderOptions[number];

export const sortOrderLabels: Record<SortOrderOption, string> = {
    application_type: "Application Type",
    submitted_newest: "Submitted: Newest",
    submitted_oldest: "Submitted: Oldest",
    created_newest: "Created: Newest",
    created_oldest: "Created: Oldest",
    updated_newest: "Updated: Newest",
    updated_oldest: "Updated: Oldest",
};

/**
 * Check if any applications have submitted_at values.
 * Used to conditionally show submission date sort options.
 */
export const hasSubmittedApplications = (applications: IApplicationData[]): boolean => {
    return _.some(applications, (app) => app.submitted_at !== null);
};
export const isSortOrderOption = (value: string): value is SortOrderOption => {
    return sortOrderOptions.includes(value as SortOrderOption);
};

/**
 * Retrieves the initial sort order from localStorage, falling back to the provided default.
 * Use this to initialise sort state with persisted user preferences.
 * 
 * @param storageKey - LocalStorage key where the sort preference is stored
 * @param defaultSortOrder - Default sort order to use if no valid stored value exists
 * @returns The stored sort order if valid, otherwise the provided default sort order
 */
export const getInitialSortOrder = (storageKey: string, defaultSortOrder: SortOrderOption): SortOrderOption => {
    const storedValue = LocalStorage.getValue<string>(storageKey);
    if (storedValue && isSortOrderOption(storedValue)) {
        return storedValue;
    }
    return defaultSortOrder;
};

/**
 * Efficiently sorts applications by the specified order.
 * No longer requires processBySlug Map since sort orders are now in the application data.
 * 
 * @param applications - Applications to sort
 * @param sortOrder - Sort order preference
 * @returns Sorted copy of applications
 */
export const sortApplications = (
    applications: IApplicationData[],
    sortOrder: SortOrderOption,
): IApplicationData[] => {
    const sorted = [...applications];

    if (sortOrder === "submitted_newest") {
        // Sort by submitted_at descending, placing unsubmitted applications at the end
        sorted.sort((a, b) => {
            if (a.submitted_at === null && b.submitted_at === null) return 0;
            if (a.submitted_at === null) return 1; // unsubmitted goes last
            if (b.submitted_at === null) return -1; // unsubmitted goes last
            return new Date(b.submitted_at).getTime() - new Date(a.submitted_at).getTime();
        });
        return sorted;
    }

    if (sortOrder === "submitted_oldest") {
        // Sort by submitted_at ascending, placing unsubmitted applications at the end
        sorted.sort((a, b) => {
            if (a.submitted_at === null && b.submitted_at === null) return 0;
            if (a.submitted_at === null) return 1; // unsubmitted goes last
            if (b.submitted_at === null) return -1; // unsubmitted goes last
            return new Date(a.submitted_at).getTime() - new Date(b.submitted_at).getTime();
        });
        return sorted;
    }

    if (sortOrder === "application_type") {
        // Sort by process order (primary), then questionnaire sort order (secondary).
        // This groups applications by process type, with questionnaires ordered consistently.
        sorted.sort((a, b) => {
            if (a.process_sort_order !== b.process_sort_order) {
                return a.process_sort_order - b.process_sort_order;
            }

            // Same process: sort by questionnaire sort order
            return a.questionnaire_sort_order - b.questionnaire_sort_order;
        });
        return sorted;
    }

    if (sortOrder === "created_newest") {
        sorted.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
        return sorted;
    }

    if (sortOrder === "created_oldest") {
        sorted.sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());
        return sorted;
    }

    if (sortOrder === "updated_newest") {
        sorted.sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime());
        return sorted;
    }

    // Default: "updated_oldest"
    sorted.sort((a, b) => new Date(a.updated_at).getTime() - new Date(b.updated_at).getTime());
    return sorted;
};

/**
 * Get available sort options based on whether applications are submitted.
 * Submitted sorting options (submitted_newest, submitted_oldest) only appear
 * when there are submitted applications in the list.
 */
export const getAvailableSortOptions = (applications: IApplicationData[]): SortOrderOption[] => {
    if (hasSubmittedApplications(applications)) {
        return [...sortOrderOptions];
    }
    // Filter out submitted sort options for lists without submitted applications
    return sortOrderOptions.filter((option) => option !== "submitted_newest" && option !== "submitted_oldest");
};

interface ApplicationSortControlProps {
    value: SortOrderOption;
    onChange: (sortOrder: SortOrderOption) => void;
    isDisabled?: boolean;
    controlId?: string;
    availableOptions?: readonly SortOrderOption[];
}

/**
 * Reusable sort control component for applications.
 * Provides a dropdown menu to select application sorting order.
 * 
 * @param value - Current sort order
 * @param onChange - Callback when sort order changes
 * @param isDisabled - Whether the control is disabled
 * @param controlId - HTML id for the select control (optional, defaults to 'applications-sort')
 * @param availableOptions - Optional list of sort options to display (defaults to all sortOrderOptions)
 */
export const ApplicationSortControl = ({
    value,
    onChange,
    isDisabled = false,
    controlId = 'applications-sort',
    availableOptions = sortOrderOptions,
}: ApplicationSortControlProps) => {
    return (
        <FormControl size="small" disabled={isDisabled}>
            <Select
                id={controlId}
                value={value}
                className="min-w-55"
                displayEmpty
                onChange={(event) => onChange(event.target.value as SortOrderOption)}
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
                {availableOptions.map((option) => (
                    <MenuItem key={option} value={option}>
                        {sortOrderLabels[option]}
                    </MenuItem>
                ))}
            </Select>
        </FormControl>
    );
};
