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

vi.mock("../../../../../components/layout/main/ApplicationCard", () => ({
  ApplicationCard: ({ application }: { application: { internal_id: string } }) => (
    <div data-testid="assessment-card">{application.internal_id}</div>
  ),
}));

import { ApplicationAssessment } from "../../../../../components/layout/main/Assessment";


describe("ApplicationAssessment", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useLoaderDataMock.mockReturnValue({
      processes: [makeProcess({ slug: "s40", can_review: true })],
      applications: Promise.resolve([]),
    });
  });

  it("renders loading state while queue is resolving", () => {
    useResolvedPromiseMock.mockReturnValue([[], true]);

    render(<ApplicationAssessment />);

    expect(screen.getByText("Loading applications...")).toBeInTheDocument();
  });

  it("renders empty state when no assessment applications exist", () => {
    useResolvedPromiseMock.mockReturnValue([[], false]);

    render(<ApplicationAssessment />);

    expect(screen.getByText("No items found")).toBeInTheDocument();
  });

  it("orders queue by workflow priority then created_at ascending within same status", () => {
    useResolvedPromiseMock.mockReturnValue([
      [
        makeApplication({ internal_id: "under-review", status: "UNDER_REVIEW", created_at: "2026-05-11T00:00:00Z" }),
        makeApplication({ key: "22222222-2222-2222-2222-222222222222", internal_id: "submitted-later", status: "SUBMITTED", created_at: "2026-05-12T00:00:00Z" }),
        makeApplication({ key: "33333333-3333-3333-3333-333333333333", internal_id: "submitted-earlier", status: "SUBMITTED", created_at: "2026-05-10T00:00:00Z" }),
      ],
      false,
    ]);

    render(<ApplicationAssessment />);

    const ordered = screen.getAllByTestId("assessment-card").map((node) => node.textContent);
    expect(ordered).toEqual(["submitted-earlier", "submitted-later", "under-review"]);
  });
});
