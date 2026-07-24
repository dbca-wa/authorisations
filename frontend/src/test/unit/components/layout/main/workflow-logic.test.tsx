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
        const { rerender } = render(
            <ApplicationCard 
                process={makeProcess()} 
                application={makeApplication({ status: "DRAFT" })} 
            />
        );
        expect(screen.getByRole("button", { name: "Continue" })).toBeInTheDocument();

        // Any other state should not show "Continue"
        const nonEditable: ApplicationStatus[] = ["SUBMITTED", "UNDER_REVIEW", "UNDER_ASSESSMENT", "APPROVED"];
        nonEditable.forEach(status => {
            rerender(
                <ApplicationCard 
                    process={makeProcess()} 
                    application={makeApplication({ status })} 
                />
            );
            expect(screen.queryByRole("button", { name: "Continue" })).not.toBeInTheDocument();
        });
    });

    /**
     * Verifies that the download link is NOT visible for DRAFT applications.
     * Applicants should only be able to download a PDF once they have submitted
     * or finalised the application.
     */
    it("identifies appropriate statuses as downloadable", () => {
        const { rerender } = render(
            <ApplicationCard 
                process={makeProcess()} 
                application={makeApplication({ status: "SUBMITTED" })} 
            />
        );
        expect(screen.getByRole("link", { name: "Download application PDF" })).toBeInTheDocument();

        // DRAFT should not be downloadable
        rerender(
            <ApplicationCard 
                process={makeProcess()} 
                application={makeApplication({ status: "DRAFT" })} 
            />
        );
        expect(screen.queryByRole("link", { name: "Download application PDF" })).not.toBeInTheDocument();
    });

    /**
     * Verifies the mapping between application status and the visual stepper index.
     * Accurate mapping ensures the applicant has a clear sense of where their
     * application is in the lifecycle.
     */
    it("correctly maps workflow statuses to stepper steps", () => {
        const testCases: Array<{ status: ApplicationStatus; step: number }> = [
            { status: "DRAFT", step: 0 },
            { status: "DISCARDED", step: 0 },  // Terminal during draft phase
            { status: "SUBMITTED", step: 1 },
            { status: "UNDER_REVIEW", step: 2 },
            { status: "WITHDRAWN", step: 2 },  // Terminal after submission
            { status: "UNDER_ASSESSMENT", step: 3 },
            { status: "APPROVED", step: 4 },
            { status: "APPROVED_WITH_CONDITIONS", step: 4 },
            { status: "DEFERRED", step: 4 },
            { status: "REJECTED", step: 4 }
        ];

        // This effectively tests the statusToActiveStep mapping record in ApplicationCard
        testCases.forEach(({ status, step }) => {
            const { container } = render(
                <ApplicationCard 
                    process={makeProcess()} 
                    application={makeApplication({ status })} 
                />
            );
            
            // Check for the 'Mui-active' class on the expected step
            const steps = container.querySelectorAll(".MuiStep-root");
            expect(steps[step].querySelector(".MuiStepLabel-label")).toHaveClass("Mui-active");
        });
    });
});
