import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ApplicationSortControl, sortApplications, isSortOrderOption, sortOrderLabels, sortOrderOptions } from "../../../../../components/layout/main/applicationUtils";
import { makeApplication } from "../../../fixtures";

describe("Application Sorting Utilities", () => {
    describe("isSortOrderOption", () => {
        it("returns true for valid sort order options", () => {
            expect(isSortOrderOption("application_type")).toBe(true);
            expect(isSortOrderOption("newest")).toBe(true);
            expect(isSortOrderOption("oldest")).toBe(true);
            expect(isSortOrderOption("recently_updated")).toBe(true);
            expect(isSortOrderOption("least_recently_updated")).toBe(true);
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
            expect(sortOrderLabels.application_type).toBe("Application type");
            expect(sortOrderLabels.newest).toBe("Newest");
            expect(sortOrderLabels.oldest).toBe("Oldest");
            expect(sortOrderLabels.recently_updated).toBe("Recently updated");
            expect(sortOrderLabels.least_recently_updated).toBe("Least recently updated");
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

        it("sorts by 'newest' (most recent created_at first)", () => {
            const sorted = sortApplications([app1, app2, app3], "newest");
            expect(sorted.map((a) => a.key)).toEqual(["k3", "k2", "k1"]);
        });

        it("sorts by 'oldest' (oldest created_at first)", () => {
            const sorted = sortApplications([app3, app1, app2], "oldest");
            expect(sorted.map((a) => a.key)).toEqual(["k1", "k2", "k3"]);
        });

        it("sorts by 'recently_updated' (most recent updated_at first)", () => {
            const sorted = sortApplications([app1, app3, app2], "recently_updated");
            expect(sorted.map((a) => a.key)).toEqual(["k3", "k2", "k1"]);
        });

        it("sorts by 'least_recently_updated' (oldest updated_at first)", () => {
            const sorted = sortApplications([app3, app2, app1], "least_recently_updated");
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
            sortApplications(original, "newest");
            expect(JSON.stringify(original.map(a => a.key))).toBe(originalCopy);
        });

        it("handles empty applications array", () => {
            const sorted = sortApplications([], "newest");
            expect(sorted).toEqual([]);
        });

        it("handles single application", () => {
            const sorted = sortApplications([app1], "newest");
            expect(sorted).toEqual([app1]);
        });
    });
});

describe("ApplicationSortControl Component", () => {
    it("renders the sort control with current value", () => {
        const handleChange = vi.fn();
        render(
            <ApplicationSortControl
                value="newest"
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
                value="oldest"
                onChange={handleChange}
            />
        );

        expect(screen.getByText("Oldest")).toBeInTheDocument();
    });

    it("calls onChange when a different sort option is selected", () => {
        const handleChange = vi.fn();
        render(
            <ApplicationSortControl
                value="newest"
                onChange={handleChange}
            />
        );

        const select = screen.getByRole("combobox", { name: "Sort applications" });
        fireEvent.mouseDown(select);
        const recentlyUpdatedOption = screen.getByText("Recently updated");
        fireEvent.click(recentlyUpdatedOption);

        expect(handleChange).toHaveBeenCalledWith("recently_updated");
    });

    it("renders all sort order options in the menu", () => {
        const handleChange = vi.fn();
        render(
            <ApplicationSortControl
                value="newest"
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
                value="newest"
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
                value="newest"
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
                value="newest"
                onChange={handleChange}
            />
        );

        const select = screen.getByRole("combobox", { name: "Sort applications" });
        expect(select).toHaveAttribute("id", "applications-sort");
    });
});
