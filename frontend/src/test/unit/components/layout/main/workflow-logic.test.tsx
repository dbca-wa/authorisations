import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { ApplicationStatus } from "../../../../../context/types/Application";
import { ApplicationCard } from "../../../../../components/layout/main/ApplicationCard";
import { makeApplication, makeProcess } from "../../../fixtures";

// Mock useSnackbar to avoid "useSnackbar must be used within a SnackbarProvider" error
vi.mock("../../../../../context/Hooks", async () => {
    const actual = await vi.importActual<typeof import("../../../../../context/Hooks")>("../../../../../context/Hooks");
    return {
        ...actual,
        useSnackbar: () => ({ showSnackbar: vi.fn() }),
    };
});

/**
 * Validates ApplicationCard logic against the STATUS-WORKFLOW definitions.
 * This ensures that the frontend correctly reflects the state machine logic
 * defined in the business documentation.
 */
describe("Application Workflow Frontend Logic", () => {
    
    /**
     * Verifies that 'Continue' is only visible when an application is in DRAFT.
     * This prevents applicants from trying to edit applications that are already
     * submitted or under review.
     */
    it("identifies DRAFT as the only editable status for applicants", () => {
        // Test that DRAFT shows Continue button
        const { unmount } = render(
            <ApplicationCard 
                process={makeProcess()} 
                application={makeApplication({ status: "DRAFT" })}
                onStatusChanged={vi.fn()}
            />
        );
        expect(screen.getByRole("button", { name: "Continue" })).toBeInTheDocument();
        unmount();

        // Test that non-DRAFT statuses do NOT show Continue button
        const nonEditable: ApplicationStatus[] = ["SUBMITTED", "UNDER_REVIEW", "UNDER_ASSESSMENT", "APPROVED"];
        nonEditable.forEach(status => {
            render(
                <ApplicationCard 
                    process={makeProcess()} 
                    application={makeApplication({ status })}
                    onStatusChanged={vi.fn()}
                />
            );
            expect(screen.queryByRole("button", { name: "Continue" })).not.toBeInTheDocument();
            unmount();
        });
    });

    /**
     * Verifies that the download link is NOT visible for DRAFT applications.
     * Applicants should only be able to download a PDF once they have submitted
     * or finalised the application.
     */
    it("identifies appropriate statuses as downloadable", () => {
        // Test that SUBMITTED shows Download link
        const { unmount } = render(
            <ApplicationCard 
                process={makeProcess()} 
                application={makeApplication({ status: "SUBMITTED" })}
                onStatusChanged={vi.fn()}
            />
        );
        expect(screen.getByRole("link", { name: "Download application PDF" })).toBeInTheDocument();
        unmount();

        // Test that DRAFT does NOT show Download link
        render(
            <ApplicationCard 
                process={makeProcess()} 
                application={makeApplication({ status: "DRAFT" })}
                onStatusChanged={vi.fn()}
            />
        );
        expect(screen.queryByRole("link", { name: "Download application PDF" })).not.toBeInTheDocument();
    });

    /**
     * Verifies the mapping between application status and the visual stepper index.
     * Accurate mapping ensures the applicant has a clear sense of where their
     * application is in the lifecycle.
     *
     * Note: Terminated statuses (DISCARDED, WITHDRAWN) display an Alert instead of
     * the Stepper, so they are not tested here. Only active statuses are validated.
     */
    it("correctly maps workflow statuses to stepper steps", () => {
        // Test cases for active (non-terminated) statuses only
        // Terminated statuses show an Alert instead of Stepper, so stepper steps don't exist in DOM
        const testCases: Array<{ status: ApplicationStatus; step: number }> = [
            { status: "DRAFT", step: 0 },
            { status: "SUBMITTED", step: 1 },
            { status: "UNDER_REVIEW", step: 2 },
            { status: "UNDER_ASSESSMENT", step: 3 },
            { status: "APPROVED", step: 4 },
            { status: "APPROVED_WITH_CONDITIONS", step: 4 },
            { status: "DEFERRED", step: 4 },
            { status: "REJECTED", step: 4 }
        ];

        testCases.forEach(({ status, step }) => {
            const { container, unmount } = render(
                <ApplicationCard 
                    process={makeProcess()} 
                    application={makeApplication({ status })}
                    onStatusChanged={vi.fn()}
                />
            );
            
            // Query for step elements using DOM classes and verify the correct step is active
            const steps = container.querySelectorAll(".MuiStep-root");
            expect(steps.length).toBe(5);
            
            // The active step has the "Mui-active" class on its icon container
            const activeStepIcon = steps[step].querySelector(".MuiStepIcon-root.Mui-active");
            expect(activeStepIcon).toBeInTheDocument();
            
            unmount();
        });
    });
});
