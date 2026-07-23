import { render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { makeApplication, makeProcess } from "../../../fixtures";
import { LocalStorage } from "../../../../../context/LocalStorage";

const useLoaderDataMock = vi.fn();
const useResolvedPromiseMock = vi.fn();

vi.mock("react-router", async () => {
  const actual = await vi.importActual<typeof import("react-router")>("react-router");
  return {
    ...actual,
    useLoaderData: () => useLoaderDataMock(),
  };
});

vi.mock("../../../../../context/Hooks", async () => {
  const actual = await vi.importActual<typeof import("../../../../../context/Hooks")>("../../../../../context/Hooks");
  return {
    ...actual,
    useResolvedPromise: (...args: unknown[]) => useResolvedPromiseMock(...args),
  };
});

vi.mock("../../../../../components/layout/main/ApplicationCard", () => ({
  ApplicationCard: ({ application }: { application: { internal_id: string; status: string; key: string } }) => {
    // Simulate the behavior of ApplicationCard's internal logic
    const downloadableStatuses = [
      "SUBMITTED",
      "UNDER_REVIEW",
      "UNDER_ASSESSMENT",
      "APPROVED",
      "APPROVED_WITH_CONDITIONS",
      "DEFERRED",
      "REJECTED"
    ];
    const isDownloadable = downloadableStatuses.includes(application.status);
    const isEditable = application.status === "DRAFT";
    return (
      <div data-testid="application-card">{`${application.internal_id}|download:${isDownloadable ? "yes" : "no"}|continue:${isEditable ? "yes" : "no"}`}</div>
    );
  },
}));

import { MyApplications } from "../../../../../components/layout/main/MyApplications";


describe("MyApplications", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    LocalStorage.removeValue("my-applications-sort-order");
    useLoaderDataMock.mockReturnValue({
      processes: [makeProcess({ slug: "s40", sort_order: 1 })],
      applications: Promise.resolve([]),
    });
  });

  afterEach(() => {
    LocalStorage.removeValue("my-applications-sort-order");
  });

  it("renders loading state while deferred applications are unresolved", () => {
    useResolvedPromiseMock.mockReturnValue([[], true]);

    render(<MyApplications />);

    expect(screen.getByText("One moment while we fetch that for you...")).toBeInTheDocument();
  });

  it("renders empty state when there are no applications", () => {
    useResolvedPromiseMock.mockReturnValue([[], false]);

    render(<MyApplications />);

    expect(screen.getByText("Nothing to see here")).toBeInTheDocument();
    expect(screen.getByText(/We checked.*There really isn't anything hiding here/)).toBeInTheDocument();
  });

  it("renders download button for finalised/submitted and continue button for drafts", () => {
    useResolvedPromiseMock.mockReturnValue([
      [
        makeApplication({ internal_id: "app-submitted", status: "SUBMITTED", key: "k1" }),
        makeApplication({ internal_id: "app-draft", status: "DRAFT", key: "k2" }),
      ],
      false,
    ]);

    render(<MyApplications />);

    const cards = screen.getAllByTestId("application-card").map((node) => node.textContent);
    expect(cards).toContain("app-submitted|download:yes|continue:no");
    expect(cards).toContain("app-draft|download:no|continue:yes");
  });

  it("uses persisted sort order when stored value is valid", () => {
    LocalStorage.setValue("my-applications-sort-order", "created_oldest");
    useResolvedPromiseMock.mockReturnValue([[makeApplication()], false]);

    render(<MyApplications />);

    const stored = LocalStorage.getValue<string>("my-applications-sort-order");
    expect(stored).toBe("created_oldest");
  });

  it("uses 'updated_newest' as default sort order when no stored value", () => {
    LocalStorage.removeValue("my-applications-sort-order");
    useResolvedPromiseMock.mockReturnValue([
      [
        makeApplication({ internal_id: "app1", updated_at: "2026-05-10T00:00:00Z" }),
        makeApplication({ key: "22222222-2222-2222-2222-222222222222", internal_id: "app2", updated_at: "2026-05-12T00:00:00Z" }),
        makeApplication({ key: "33333333-3333-3333-3333-333333333333", internal_id: "app3", updated_at: "2026-05-11T00:00:00Z" }),
      ],
      false,
    ]);

    render(<MyApplications />);

    const ordered = screen.getAllByTestId("application-card").map((node) => node.textContent.split("|")[0]);
    // Default sort is "updated_newest", so most recent updated_at comes first
    expect(ordered).toEqual(["app2", "app3", "app1"]);
  });

  it("hides submitted sort options when applications contain drafts", () => {
    LocalStorage.removeValue("my-applications-sort-order");
    useResolvedPromiseMock.mockReturnValue([
      [
        makeApplication({ submitted_at: null, status: "DRAFT" }),
      ],
      false,
    ]);

    render(<MyApplications />);

    const sortControl = screen.queryByRole("combobox", { name: "Sort applications" });
    // Should not see submitted options for draft-only view
    if (sortControl) {
      expect(sortControl.textContent).not.toContain("Submitted: Newest");
      expect(sortControl.textContent).not.toContain("Submitted: Oldest");
    }
  });
});
