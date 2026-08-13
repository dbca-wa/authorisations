import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { makeApplication, makeProcess } from "../../../fixtures";

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

vi.mock("../../../../../components/layout/main/ReviewCard", () => ({
  ReviewCard: ({ application }: { application: { internal_id: string } }) => (
    <div data-testid="review-card">{application.internal_id}</div>
  ),
}));

import { ApplicationReview } from "../../../../../components/layout/main/Review";


describe("ApplicationReview", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useLoaderDataMock.mockReturnValue({
      processes: [makeProcess({ slug: "s40", can_review: true })],
      applications: Promise.resolve([]),
    });
  });

  it("renders loading state while queue is resolving", () => {
    useResolvedPromiseMock.mockReturnValue([[], true]);

    render(<ApplicationReview />);

    expect(screen.getByText("One moment while we fetch that for you...")).toBeInTheDocument();
  });

  it("renders empty state when no review applications exist", () => {
    useResolvedPromiseMock.mockReturnValue([[], false]);

    render(<ApplicationReview />);

    expect(screen.getByText("Nothing to see here")).toBeInTheDocument();
    expect(screen.getByText(/We checked.*There really isn't anything hiding here/)).toBeInTheDocument();
  });

  it("orders queue by submitted_oldest (default sort order for review)", () => {
    useResolvedPromiseMock.mockReturnValue([
      [
        makeApplication({ internal_id: "app1", status: "SUBMITTED", submitted_at: "2026-05-12T00:00:00Z" }),
        makeApplication({ key: "22222222-2222-2222-2222-222222222222", internal_id: "app2", status: "SUBMITTED", submitted_at: "2026-05-10T00:00:00Z" }),
        makeApplication({ key: "33333333-3333-3333-3333-333333333333", internal_id: "app3", status: "SUBMITTED", submitted_at: "2026-05-11T00:00:00Z" }),
      ],
      false,
    ]);

    render(<ApplicationReview />);

    const ordered = screen.getAllByTestId("review-card").map((node) => node.textContent);
    // Default sort for review is "submitted_oldest", so oldest submitted_at comes first
    expect(ordered).toEqual(["app2", "app3", "app1"]);
  });

  it("renders sort control with submitted options when applications have submitted_at", () => {
    useResolvedPromiseMock.mockReturnValue([
      [
        makeApplication({ submitted_at: "2026-05-10T00:00:00Z" }),
        makeApplication({ key: "22222222-2222-2222-2222-222222222222", submitted_at: "2026-05-11T00:00:00Z" }),
      ],
      false,
    ]);

    render(<ApplicationReview />);

    // Sort control should be visible with submitted options
    expect(screen.getByRole("combobox", { name: "Sort applications" })).toBeInTheDocument();
    expect(screen.getByText("Submitted: Oldest")).toBeInTheDocument();
  });
});
