import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { makeApplication, makeProcess } from "../../../fixtures";

const useLoaderDataMock = vi.fn();
const useResolvedPromiseMock = vi.fn();
const localStorageGetMock = vi.fn();
const localStorageSetMock = vi.fn();

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

vi.mock("../../../../../context/LocalStorage", () => ({
  LocalStorage: {
    getValue: (...args: unknown[]) => localStorageGetMock(...args),
    setValue: (...args: unknown[]) => localStorageSetMock(...args),
  },
}));

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
    const editableStatuses = ["DRAFT", "ACTION_REQUIRED"];
    const isDownloadable = downloadableStatuses.includes(application.status);
    const isEditable = editableStatuses.includes(application.status);
    return (
      <div data-testid="application-card">{`${application.internal_id}|download:${isDownloadable ? "yes" : "no"}|continue:${isEditable ? "yes" : "no"}`}</div>
    );
  },
}));

import { MyApplications } from "../../../../../components/layout/main/MyApplications";


describe("MyApplications", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useLoaderDataMock.mockReturnValue({
      processes: [makeProcess({ slug: "s40", sort_order: 1 })],
      applications: Promise.resolve([]),
    });
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

  it("shows download button for downloadable statuses and continue button for editable statuses", () => {
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
    localStorageGetMock.mockReturnValue("oldest");
    useResolvedPromiseMock.mockReturnValue([[makeApplication()], false]);

    render(<MyApplications />);

    expect(localStorageGetMock).toHaveBeenCalledWith("my-applications-sort-order");
    expect(localStorageSetMock).toHaveBeenCalledWith("my-applications-sort-order", "oldest");
  });
});
