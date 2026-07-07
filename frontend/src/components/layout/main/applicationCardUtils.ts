import type { ApplicationStatus, IApplicationData } from "../../../context/types/Application";
import dayjs from 'dayjs';
import relativeTime from "dayjs/plugin/relativeTime";

// Enable relative date labels like "2 days ago" for card metadata.
dayjs.extend(relativeTime);

export const applicationSteps = [
    "Application",
    "Submitted",
    "Review",
    "Assessment",
    "Decision",
] as const;

export const statusToActiveStep: Record<ApplicationStatus, number> = {
    DRAFT: 0,
    DISCARDED: 0,           // Terminated during drafting — never submitted.
    ACTION_REQUIRED: 0,
    SUBMITTED: 1,
    WITHDRAWN: 2,           // Terminated after submission — reached review stage.
    UNDER_REVIEW: 2,
    UNDER_ASSESSMENT: 3,
    APPROVED: 4,
    APPROVED_WITH_CONDITIONS: 4,
    DEFERRED: 4,            // Decision deferred — may resume; shown at decision step.
    REJECTED: 4,
};

/** Statuses that represent a terminal negative outcome at their respective step. */
export const terminatedStatuses = new Set<ApplicationStatus>(["DISCARDED", "WITHDRAWN"]);

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
