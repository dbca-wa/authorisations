import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ApplicationSortControl, sortApplications, isSortOrderOption, sortOrderLabels, sortOrderOptions } from "../../../../../components/layout/main/applicationUtils";
import { makeApplication, makeProcess } from "../../../fixtures";

describe("Application Sorting Utilities", () => {
    describe("isSortOrderOption", () => {
        it("returns true for valid sort order options", () => {
            expect(isSortOrderOption("authorisation")).toBe(true);
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
            expect(sortOrderLabels.authorisation).toBe("Authorisation");
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
        });
        const app2 = makeApplication({
            key: "k2",
            created_at: new Date(baseDate.getTime() - 1 * 24 * 60 * 60 * 1000).toISOString(),
            updated_at: new Date(baseDate.getTime() - 1 * 24 * 60 * 60 * 1000).toISOString(),
            process_slug: "animal-ethics",
        });
        const app3 = makeApplication({
            key: "k3",
            created_at: baseDate.toISOString(),
            updated_at: baseDate.toISOString(),
            process_slug: "s40",
        });

        const processes = [
            makeProcess({ slug: "s40", sort_order: 1 }),
            makeProcess({ slug: "animal-ethics", sort_order: 2 }),
        ];
        const processBySlug = new Map(processes.map((p) => [p.slug, p]));

        it("sorts by 'newest' (most recent created_at first)", () => {
            const sorted = sortApplications([app1, app2, app3], "newest", processBySlug);
            expect(sorted.map((a) => a.key)).toEqual(["k3", "k2", "k1"]);
        });

        it("sorts by 'oldest' (oldest created_at first)", () => {
            const sorted = sortApplications([app3, app1, app2], "oldest", processBySlug);
            expect(sorted.map((a) => a.key)).toEqual(["k1", "k2", "k3"]);
        });

        it("sorts by 'recently_updated' (most recent updated_at first)", () => {
            const sorted = sortApplications([app1, app3, app2], "recently_updated", processBySlug);
            expect(sorted.map((a) => a.key)).toEqual(["k3", "k2", "k1"]);
        });

        it("sorts by 'least_recently_updated' (oldest updated_at first)", () => {
            const sorted = sortApplications([app3, app2, app1], "least_recently_updated", processBySlug);
            expect(sorted.map((a) => a.key)).toEqual(["k1", "k2", "k3"]);
        });

        it("sorts by 'authorisation' (process sort_order then slug)", () => {
            // When sorted by authorisation, it groups by process sort_order, then by slug within groups
            const sorted = sortApplications([app2, app3, app1], "authorisation", processBySlug);
            // s40 (sort_order: 1) comes first with k1 and k3
            // animal-ethics (sort_order: 2) comes second with k2
            const keys = sorted.map((a) => a.key);
            expect(keys.indexOf("k1")).toBeLessThan(keys.indexOf("k2"));
            expect(keys.indexOf("k3")).toBeLessThan(keys.indexOf("k2"));
        });

        it("returns a new array without modifying the original", () => {
            const original = [app1, app2, app3];
            const originalCopy = JSON.stringify(original.map(a => a.key));
            sortApplications(original, "newest", processBySlug);
            expect(JSON.stringify(original.map(a => a.key))).toBe(originalCopy);
        });

        it("handles empty applications array", () => {
            const sorted = sortApplications([], "newest", processBySlug);
            expect(sorted).toEqual([]);
        });

        it("handles single application", () => {
            const sorted = sortApplications([app1], "newest", processBySlug);
            expect(sorted).toEqual([app1]);
        });

        it("handles processes not in the processBySlug map", () => {
            const appUnknownProcess = makeApplication({
                key: "k-unknown",
                process_slug: "unknown-process",
            });
            const sorted = sortApplications([app1, appUnknownProcess], "authorisation", processBySlug);
            // Unknown processes get MAX_SAFE_INTEGER, so they come last
            expect(sorted[0].key).toEqual("k1");
            expect(sorted[1].key).toEqual("k-unknown");
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

        expect(screen.getByText(sortOrderLabels.authorisation)).toBeInTheDocument();
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
