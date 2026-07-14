/* eslint-disable react-refresh/only-export-components */
import SortIcon from '@mui/icons-material/Sort';
import Box from "@mui/material/Box";
import FormControl from "@mui/material/FormControl";
import MenuItem from "@mui/material/MenuItem";
import Select from "@mui/material/Select";
import type { ApplicationStatus, IApplicationData } from "../../../context/types/Application";
import { LocalStorage } from "../../../context/LocalStorage";
import dayjs from 'dayjs';
import relativeTime from "dayjs/plugin/relativeTime";

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
 */
export const formatRelativeDates = (application: IApplicationData) => {
    return {
        createdAtRelative: dayjs(application.created_at).fromNow(),
        updatedAtRelative: dayjs(application.updated_at).fromNow(),
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
    "created_newest",
    "created_oldest",
    "updated_newest",
    "updated_oldest",
] as const;

export type SortOrderOption = typeof sortOrderOptions[number];

export const defaultSortOrder: SortOrderOption = "created_newest";

export const sortOrderLabels: Record<SortOrderOption, string> = {
    application_type: "Application Type",
    created_newest: "Created: Newest",
    created_oldest: "Created: Oldest",
    updated_newest: "Updated: Newest",
    updated_oldest: "Updated: Oldest",
};

/**
 * Type guard to validate if a value is a valid SortOrderOption.
 */
export const isSortOrderOption = (value: string): value is SortOrderOption => {
    return sortOrderOptions.includes(value as SortOrderOption);
};

/**
 * Retrieves the initial sort order from localStorage, falling back to the default.
 * Use this to initialise sort state with persisted user preferences.
 * 
 * @param storageKey - LocalStorage key where the sort preference is stored
 * @returns The stored sort order if valid, otherwise the default sort order
 */
export const getInitialSortOrder = (storageKey: string): SortOrderOption => {
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

// ============================================================================
// Application Sort Control Component
// ============================================================================

interface ApplicationSortControlProps {
    value: SortOrderOption;
    onChange: (sortOrder: SortOrderOption) => void;
    isDisabled?: boolean;
    controlId?: string;
}

/**
 * Reusable sort control component for applications.
 * Provides a dropdown menu to select application sorting order.
 * 
 * @param value - Current sort order
 * @param onChange - Callback when sort order changes
 * @param isDisabled - Whether the control is disabled
 * @param controlId - HTML id for the select control (optional, defaults to 'applications-sort')
 */
export const ApplicationSortControl = ({
    value,
    onChange,
    isDisabled = false,
    controlId = 'applications-sort',
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
                {sortOrderOptions.map((option) => (
                    <MenuItem key={option} value={option}>
                        {sortOrderLabels[option]}
                    </MenuItem>
                ))}
            </Select>
        </FormControl>
    );
};
