import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ApplicationSortControl, sortApplications, isSortOrderOption, sortOrderLabels, sortOrderOptions, getInitialSortOrder, getAvailableSortOptions, hasSubmittedApplications } from "../../../../../components/layout/main/applicationUtils";
import { makeApplication } from "../../../fixtures";
import { LocalStorage } from "../../../../../context/LocalStorage";

describe("Helper Functions", () => {
    describe("hasSubmittedApplications", () => {
        it("returns true when at least one application is submitted", () => {
            const apps = [
                makeApplication({ submitted_at: null }),
                makeApplication({ submitted_at: "2026-05-10T00:00:00Z" }),
            ];
            expect(hasSubmittedApplications(apps)).toBe(true);
        });

        it("returns false when no applications are submitted", () => {
            const apps = [
                makeApplication({ submitted_at: null }),
                makeApplication({ submitted_at: null }),
            ];
            expect(hasSubmittedApplications(apps)).toBe(false);
        });

        it("returns false for empty array", () => {
            expect(hasSubmittedApplications([])).toBe(false);
        });
    });

    describe("getAvailableSortOptions", () => {
        it("includes submitted sort options when applications are submitted", () => {
            const apps = [makeApplication({ submitted_at: "2026-05-10T00:00:00Z" })];
            const available = getAvailableSortOptions(apps);
            expect(available).toContain("submitted_newest");
            expect(available).toContain("submitted_oldest");
        });

        it("excludes submitted sort options when no applications are submitted", () => {
            const apps = [makeApplication({ submitted_at: null })];
            const available = getAvailableSortOptions(apps);
            expect(available).not.toContain("submitted_newest");
            expect(available).not.toContain("submitted_oldest");
        });

        it("includes all other sort options regardless of submission status", () => {
            const apps = [makeApplication({ submitted_at: null })];
            const available = getAvailableSortOptions(apps);
            expect(available).toContain("application_type");
            expect(available).toContain("created_newest");
            expect(available).toContain("created_oldest");
            expect(available).toContain("updated_newest");
            expect(available).toContain("updated_oldest");
        });
    });

    describe("getInitialSortOrder", () => {
        afterEach(() => {
            LocalStorage.removeValue("test-sort-key");
        });

        it("returns stored sort order when valid", () => {
            LocalStorage.setValue("test-sort-key", "created_oldest");
            const sortOrder = getInitialSortOrder("test-sort-key", "updated_newest");
            expect(sortOrder).toBe("created_oldest");
        });

        it("returns default sort order when no stored value", () => {
            const sortOrder = getInitialSortOrder("test-sort-key", "updated_newest");
            expect(sortOrder).toBe("updated_newest");
        });

        it("returns default sort order when stored value is invalid", () => {
            LocalStorage.setValue("test-sort-key", "invalid_sort_option");
            const sortOrder = getInitialSortOrder("test-sort-key", "submitted_oldest");
            expect(sortOrder).toBe("submitted_oldest");
        });
    });
});

describe("Application Sorting Utilities", () => {
    describe("isSortOrderOption", () => {
        it("returns true for valid sort order options", () => {
            expect(isSortOrderOption("application_type")).toBe(true);
            expect(isSortOrderOption("submitted_newest")).toBe(true);
            expect(isSortOrderOption("submitted_oldest")).toBe(true);
            expect(isSortOrderOption("created_newest")).toBe(true);
            expect(isSortOrderOption("created_oldest")).toBe(true);
            expect(isSortOrderOption("updated_newest")).toBe(true);
            expect(isSortOrderOption("updated_oldest")).toBe(true);
        });

        it("returns false for invalid sort order options", () => {
            expect(isSortOrderOption("invalid")).toBe(false);
            expect(isSortOrderOption("")).toBe(false);
            expect(isSortOrderOption("NEWEST")).toBe(false);
        });
    });

    describe("sortOrderLabels", () => {
        it("provides display labels for all sort order options", () => {
            sortOrderOptions.forEach((option) => {
                expect(sortOrderLabels[option]).toBeDefined();
                expect(sortOrderLabels[option]).toBeTypeOf("string");
                expect(sortOrderLabels[option].length).toBeGreaterThan(0);
            });
        });

        it("has consistent label formatting", () => {
            expect(sortOrderLabels.application_type).toBe("Application Type");
            expect(sortOrderLabels.submitted_newest).toBe("Submitted: Newest");
            expect(sortOrderLabels.submitted_oldest).toBe("Submitted: Oldest");
            expect(sortOrderLabels.created_newest).toBe("Created: Newest");
            expect(sortOrderLabels.created_oldest).toBe("Created: Oldest");
            expect(sortOrderLabels.updated_newest).toBe("Updated: Newest");
            expect(sortOrderLabels.updated_oldest).toBe("Updated: Oldest");
        });
    });

    describe("sortApplications", () => {
        const baseDate = new Date("2024-01-01T00:00:00Z");
        const app1 = makeApplication({
            key: "k1",
            created_at: new Date(baseDate.getTime() - 2 * 24 * 60 * 60 * 1000).toISOString(),
            updated_at: new Date(baseDate.getTime() - 2 * 24 * 60 * 60 * 1000).toISOString(),
            process_slug: "s40",
            process_sort_order: 1,
            questionnaire_sort_order: 2,
        });
        const app2 = makeApplication({
            key: "k2",
            created_at: new Date(baseDate.getTime() - 1 * 24 * 60 * 60 * 1000).toISOString(),
            updated_at: new Date(baseDate.getTime() - 1 * 24 * 60 * 60 * 1000).toISOString(),
            process_slug: "animal-ethics",
            process_sort_order: 2,
            questionnaire_sort_order: 1,
        });
        const app3 = makeApplication({
            key: "k3",
            created_at: baseDate.toISOString(),
            updated_at: baseDate.toISOString(),
            process_slug: "s40",
            process_sort_order: 1,
            questionnaire_sort_order: 1,
        });

        it("sorts by 'submitted_newest' (most recent submitted_at first)", () => {
            const submitted1 = makeApplication({
                key: "k1",
                submitted_at: "2026-05-10T00:00:00Z",
            });
            const submitted2 = makeApplication({
                key: "k2",
                submitted_at: "2026-05-12T00:00:00Z",
            });
            const draft = makeApplication({
                key: "k3",
                submitted_at: null,
            });

            const sorted = sortApplications([submitted1, draft, submitted2], "submitted_newest");
            expect(sorted.map((a) => a.key)).toEqual(["k2", "k1", "k3"]);
        });

        it("sorts by 'submitted_oldest' (oldest submitted_at first)", () => {
            const submitted1 = makeApplication({
                key: "k1",
                submitted_at: "2026-05-10T00:00:00Z",
            });
            const submitted2 = makeApplication({
                key: "k2",
                submitted_at: "2026-05-12T00:00:00Z",
            });
            const draft = makeApplication({
                key: "k3",
                submitted_at: null,
            });

            const sorted = sortApplications([submitted2, draft, submitted1], "submitted_oldest");
            expect(sorted.map((a) => a.key)).toEqual(["k1", "k2", "k3"]);
        });

        it("sorts by 'created_newest' (most recent created_at first)", () => {
            const sorted = sortApplications([app1, app2, app3], "created_newest");
            expect(sorted.map((a) => a.key)).toEqual(["k3", "k2", "k1"]);
        });

        it("sorts by 'created_oldest' (oldest created_at first)", () => {
            const sorted = sortApplications([app3, app1, app2], "created_oldest");
            expect(sorted.map((a) => a.key)).toEqual(["k1", "k2", "k3"]);
        });

        it("sorts by 'updated_newest' (most recent updated_at first)", () => {
            const sorted = sortApplications([app1, app3, app2], "updated_newest");
            expect(sorted.map((a) => a.key)).toEqual(["k3", "k2", "k1"]);
        });

        it("sorts by 'updated_oldest' (oldest updated_at first)", () => {
            const sorted = sortApplications([app3, app2, app1], "updated_oldest");
            expect(sorted.map((a) => a.key)).toEqual(["k1", "k2", "k3"]);
        });

        it("sorts by 'application_type' (process sort_order then questionnaire sort_order)", () => {
            // s40 (process_sort_order: 1) comes first
            // Within s40: questionnaire_sort_order 1 (k3) before 2 (k1)
            // animal-ethics (process_sort_order: 2) comes last (k2)
            const sorted = sortApplications([app2, app3, app1], "application_type");
            expect(sorted.map((a) => a.key)).toEqual(["k3", "k1", "k2"]);
        });

        it("returns a new array without modifying the original", () => {
            const original = [app1, app2, app3];
            const originalCopy = JSON.stringify(original.map(a => a.key));
            sortApplications(original, "created_newest");
            expect(JSON.stringify(original.map(a => a.key))).toBe(originalCopy);
        });

        it("handles empty applications array", () => {
            const sorted = sortApplications([], "created_newest");
            expect(sorted).toEqual([]);
        });

        it("handles single application", () => {
            const sorted = sortApplications([app1], "created_newest");
            expect(sorted).toEqual([app1]);
        });
    });
});

describe("ApplicationSortControl Component", () => {
    it("renders the sort control with current value", () => {
        const handleChange = vi.fn();
        render(
            <ApplicationSortControl
                value="created_newest"
                onChange={handleChange}
            />
        );

        const selectInput = screen.getByRole("combobox", { name: "Sort applications" });
        expect(selectInput).toBeInTheDocument();
    });

    it("displays the sort icon and label", () => {
        const handleChange = vi.fn();
        render(
            <ApplicationSortControl
                value="created_oldest"
                onChange={handleChange}
            />
        );

        expect(screen.getByText("Created: Oldest")).toBeInTheDocument();
    });

    it("calls onChange when a different sort option is selected", () => {
        const handleChange = vi.fn();
        render(
            <ApplicationSortControl
                value="created_newest"
                onChange={handleChange}
            />
        );

        const select = screen.getByRole("combobox", { name: "Sort applications" });
        fireEvent.mouseDown(select);
        const updatedNewestOption = screen.getByText("Updated: Newest");
        fireEvent.click(updatedNewestOption);

        expect(handleChange).toHaveBeenCalledWith("updated_newest");
    });

    it("renders all sort order options in the menu", () => {
        const handleChange = vi.fn();
        render(
            <ApplicationSortControl
                value="created_newest"
                onChange={handleChange}
            />
        );

        const select = screen.getByRole("combobox", { name: "Sort applications" });
        fireEvent.mouseDown(select);

        expect(screen.getByText(sortOrderLabels.application_type)).toBeInTheDocument();
    });

    it("can be disabled", () => {
        const handleChange = vi.fn();
        render(
            <ApplicationSortControl
                value="created_newest"
                onChange={handleChange}
                isDisabled={true}
            />
        );

        const select = screen.getByRole("combobox", { name: "Sort applications" });
        expect(select.className).toContain("Mui-disabled");
    });

    it("accepts a custom control id", () => {
        const handleChange = vi.fn();
        render(
            <ApplicationSortControl
                value="created_newest"
                onChange={handleChange}
                controlId="custom-sort-id"
            />
        );

        const select = screen.getByRole("combobox", { name: "Sort applications" });
        expect(select).toHaveAttribute("id", "custom-sort-id");
    });

    it("defaults to 'applications-sort' control id", () => {
        const handleChange = vi.fn();
        render(
            <ApplicationSortControl
                value="created_newest"
                onChange={handleChange}
            />
        );

        const select = screen.getByRole("combobox", { name: "Sort applications" });
        expect(select).toHaveAttribute("id", "applications-sort");
    });
});
