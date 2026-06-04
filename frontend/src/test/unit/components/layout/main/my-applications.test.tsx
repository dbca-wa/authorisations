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
  ApplicationCard: ({ application, downloadUrl }: { application: { internal_id: string }; downloadUrl?: string }) => (
    <div data-testid="application-card">{`${application.internal_id}|${downloadUrl ?? "none"}`}</div>
  ),
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

    expect(screen.getByText("Loading applications...")).toBeInTheDocument();
  });

  it("renders empty state when there are no applications", () => {
    useResolvedPromiseMock.mockReturnValue([[], false]);

    render(<MyApplications />);

    expect(screen.getByText("No items found")).toBeInTheDocument();
  });

  it("shows download URL only for downloadable statuses", () => {
    useResolvedPromiseMock.mockReturnValue([
      [
        makeApplication({ internal_id: "app-submitted", status: "SUBMITTED", key: "k1" }),
        makeApplication({ internal_id: "app-draft", status: "DRAFT", key: "k2" }),
      ],
      false,
    ]);

    render(<MyApplications />);

    const cards = screen.getAllByTestId("application-card").map((node) => node.textContent);
    expect(cards).toContain("app-submitted|/d/k1");
    expect(cards).toContain("app-draft|none");
  });

  it("uses persisted sort order when stored value is valid", () => {
    localStorageGetMock.mockReturnValue("oldest");
    useResolvedPromiseMock.mockReturnValue([[makeApplication()], false]);

    render(<MyApplications />);

    expect(localStorageGetMock).toHaveBeenCalledWith("my-applications-sort-order");
    expect(localStorageSetMock).toHaveBeenCalledWith("my-applications-sort-order", "oldest");
  });
});
