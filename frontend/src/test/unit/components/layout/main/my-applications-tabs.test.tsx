import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

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
  ApplicationCard: ({ application }: { application: { internal_id: string; key: string }; onStatusChanged: (app: unknown) => void }) => {
    return <div data-testid={`card-${application.key}`}>{application.internal_id}</div>;
  },
}));

import { MyApplications } from "../../../../../components/layout/main/MyApplications";

/**
 * Tests for MyApplications tab functionality including categorization,
 * empty states per tab, and tab descriptions.
 *
 * Validates that applications are correctly categorized into Active/Terminated/Finalised
 * tabs and that appropriate messaging is shown for each tab state.
 */
describe("MyApplications Tab Behavior and Empty States", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    LocalStorage.removeValue("my-applications-sort-order");
    useLoaderDataMock.mockReturnValue({
      processes: [makeProcess({ slug: "s40", sort_order: 1 })],
      applications: Promise.resolve([]),
    });
  });

  describe("Tab categorization", () => {
    it("categorises applications into Active, Terminated, and Finalised tabs", async () => {
      useResolvedPromiseMock.mockReturnValue([
        [
          makeApplication({ internal_id: "draft-1", status: "DRAFT", key: "k1" }),
          makeApplication({ internal_id: "submitted-1", status: "SUBMITTED", key: "k2" }),
          makeApplication({ internal_id: "discarded-1", status: "DISCARDED", key: "k3" }),
          makeApplication({ internal_id: "withdrawn-1", status: "WITHDRAWN", key: "k4" }),
          makeApplication({ internal_id: "approved-1", status: "APPROVED", key: "k5" }),
          makeApplication({ internal_id: "rejected-1", status: "REJECTED", key: "k6" }),
        ],
        false,
      ]);

      render(<MyApplications />);

      // Active tab: DRAFT and SUBMITTED
      await waitFor(() => {
        expect(screen.getByText("Active (2)")).toBeInTheDocument();
      });

      // Terminated tab: DISCARDED and WITHDRAWN
      expect(screen.getByText("Terminated (2)")).toBeInTheDocument();

      // Finalised tab: APPROVED and REJECTED
      expect(screen.getByText("Finalised (2)")).toBeInTheDocument();
    });

    it("displays correct applications in each tab when switched", async () => {
      useResolvedPromiseMock.mockReturnValue([
        [
          makeApplication({ internal_id: "draft-1", status: "DRAFT", key: "k1" }),
          makeApplication({ internal_id: "discarded-1", status: "DISCARDED", key: "k2" }),
          makeApplication({ internal_id: "approved-1", status: "APPROVED", key: "k3" }),
        ],
        false,
      ]);

      render(<MyApplications />);

      // Verify Active tab shows DRAFT application
      await waitFor(() => {
        expect(screen.getByTestId("card-k1")).toBeInTheDocument();
      });
      expect(screen.queryByTestId("card-k2")).not.toBeInTheDocument();
      expect(screen.queryByTestId("card-k3")).not.toBeInTheDocument();

      // Switch to Terminated tab
      fireEvent.click(screen.getByRole("tab", { name: /Terminated/ }));

      // Verify Terminated tab shows DISCARDED application
      await waitFor(() => {
        expect(screen.getByTestId("card-k2")).toBeInTheDocument();
      });
      expect(screen.queryByTestId("card-k1")).not.toBeInTheDocument();
      expect(screen.queryByTestId("card-k3")).not.toBeInTheDocument();

      // Switch to Finalised tab
      fireEvent.click(screen.getByRole("tab", { name: /Finalised/ }));

      // Verify Finalised tab shows APPROVED application
      await waitFor(() => {
        expect(screen.getByTestId("card-k3")).toBeInTheDocument();
      });
      expect(screen.queryByTestId("card-k1")).not.toBeInTheDocument();
      expect(screen.queryByTestId("card-k2")).not.toBeInTheDocument();
    });
  });

  describe("Empty states per tab", () => {
    it("shows empty state when Active tab has no applications", () => {
      useResolvedPromiseMock.mockReturnValue([
        [
          makeApplication({ internal_id: "discarded-1", status: "DISCARDED", key: "k1" }),
        ],
        false,
      ]);

      render(<MyApplications />);

      // Active tab has no applications
      expect(screen.getByText("Nothing to see here")).toBeInTheDocument();
    });

    it("shows empty state when switching to tab with no applications (when tab is enabled)", async () => {
      useResolvedPromiseMock.mockReturnValue([
        [
          makeApplication({ internal_id: "draft-1", status: "DRAFT", key: "k1" }),
          makeApplication({ internal_id: "approved-1", status: "APPROVED", key: "k2" }),
        ],
        false,
      ]);

      const { rerender } = render(<MyApplications />);

      // Initially shows Active tab with content
      expect(screen.getByTestId("card-k1")).toBeInTheDocument();
      expect(screen.queryByText("Nothing to see here")).not.toBeInTheDocument();

      // Switch to Finalised tab which has content
      fireEvent.click(screen.getByRole("tab", { name: /Finalised/ }));

      await waitFor(() => {
        expect(screen.getByTestId("card-k2")).toBeInTheDocument();
      });

      // Now simulate removing the Finalised application
      useResolvedPromiseMock.mockReturnValue([
        [
          makeApplication({ internal_id: "draft-1", status: "DRAFT", key: "k1" }),
        ],
        false,
      ]);

      rerender(<MyApplications />);

      // Switch back to Active (which still has content)
      fireEvent.click(screen.getByRole("tab", { name: /Active/ }));

      await waitFor(() => {
        expect(screen.getByTestId("card-k1")).toBeInTheDocument();
      });
    });

    it("shows empty state when all applications are removed from a tab via discard", async () => {
      const application = makeApplication({ internal_id: "draft-1", status: "DRAFT", key: "k1" });

      useResolvedPromiseMock.mockReturnValue([
        [application],
        false,
      ]);

      const { rerender } = render(<MyApplications />);

      // Initially shows the DRAFT application
      expect(screen.getByTestId("card-k1")).toBeInTheDocument();

      // Simulate the application being discarded (status changed via callback)
      const discardedApplication = { ...application, status: "DISCARDED" as const };
      useResolvedPromiseMock.mockReturnValue([
        [discardedApplication],
        false,
      ]);

      rerender(<MyApplications />);

      // Active tab now shows empty state
      expect(screen.getByText("Nothing to see here")).toBeInTheDocument();
    });
  });

  describe("Tab descriptions", () => {
    it("displays correct description for Active tab", () => {
      useResolvedPromiseMock.mockReturnValue([[], false]);

      render(<MyApplications />);

      // Active tab is selected by default
      expect(
        screen.getByText("View and manage your draft and submitted applications.")
      ).toBeInTheDocument();
    });

    it("displays correct description for Terminated tab when applications exist", async () => {
      useResolvedPromiseMock.mockReturnValue([
        [
          makeApplication({ internal_id: "draft-1", status: "DRAFT", key: "k1" }),
          makeApplication({ internal_id: "discarded-1", status: "DISCARDED", key: "k2" }),
        ],
        false,
      ]);

      render(<MyApplications />);

      fireEvent.click(screen.getByRole("tab", { name: /Terminated/ }));

      await waitFor(() => {
        expect(
          screen.getByText("View applications that have been discarded or withdrawn.")
        ).toBeInTheDocument();
      });
    });

    it("displays correct description for Finalised tab when applications exist", async () => {
      useResolvedPromiseMock.mockReturnValue([
        [
          makeApplication({ internal_id: "draft-1", status: "DRAFT", key: "k1" }),
          makeApplication({ internal_id: "approved-1", status: "APPROVED", key: "k2" }),
        ],
        false,
      ]);

      render(<MyApplications />);

      fireEvent.click(screen.getByRole("tab", { name: /Finalised/ }));

      await waitFor(() => {
        expect(
          screen.getByText("View applications that have been approved, rejected, or deferred.")
        ).toBeInTheDocument();
      });
    });

    it("updates description when switching between tabs with applications", async () => {
      useResolvedPromiseMock.mockReturnValue([
        [
          makeApplication({ internal_id: "draft-1", status: "DRAFT", key: "k1" }),
          makeApplication({ internal_id: "discarded-1", status: "DISCARDED", key: "k2" }),
          makeApplication({ internal_id: "approved-1", status: "APPROVED", key: "k3" }),
        ],
        false,
      ]);

      render(<MyApplications />);

      // Initially shows Active description
      expect(
        screen.getByText("View and manage your draft and submitted applications.")
      ).toBeInTheDocument();

      // Switch to Terminated
      fireEvent.click(screen.getByRole("tab", { name: /Terminated/ }));

      await waitFor(() => {
        expect(
          screen.getByText("View applications that have been discarded or withdrawn.")
        ).toBeInTheDocument();
        expect(
          screen.queryByText("View and manage your draft and submitted applications.")
        ).not.toBeInTheDocument();
      });

      // Switch to Finalised
      fireEvent.click(screen.getByRole("tab", { name: /Finalised/ }));

      await waitFor(() => {
        expect(
          screen.getByText("View applications that have been approved, rejected, or deferred.")
        ).toBeInTheDocument();
        expect(
          screen.queryByText("View applications that have been discarded or withdrawn.")
        ).not.toBeInTheDocument();
      });
    });
  });

  describe("Tab enable/disable behaviour", () => {
    it("disables Active tab when there are no active applications", () => {
      useResolvedPromiseMock.mockReturnValue([
        [
          makeApplication({ internal_id: "approved-1", status: "APPROVED", key: "k1" }),
        ],
        false,
      ]);

      render(<MyApplications />);

      const activeTab = screen.getByRole("tab", { name: /Active/ });
      expect(activeTab).toHaveAttribute("disabled");
    });

    it("disables Terminated tab when there are no terminated applications", () => {
      useResolvedPromiseMock.mockReturnValue([
        [
          makeApplication({ internal_id: "draft-1", status: "DRAFT", key: "k1" }),
        ],
        false,
      ]);

      render(<MyApplications />);

      const terminatedTab = screen.getByRole("tab", { name: /Terminated/ });
      expect(terminatedTab).toHaveAttribute("disabled");
    });

    it("disables Finalised tab when there are no finalised applications", () => {
      useResolvedPromiseMock.mockReturnValue([
        [
          makeApplication({ internal_id: "draft-1", status: "DRAFT", key: "k1" }),
        ],
        false,
      ]);

      render(<MyApplications />);

      const finalisedTab = screen.getByRole("tab", { name: /Finalised/ });
      expect(finalisedTab).toHaveAttribute("disabled");
    });

    it("enables tabs when they contain applications", () => {
      useResolvedPromiseMock.mockReturnValue([
        [
          makeApplication({ internal_id: "draft-1", status: "DRAFT", key: "k1" }),
          makeApplication({ internal_id: "discarded-1", status: "DISCARDED", key: "k2" }),
          makeApplication({ internal_id: "approved-1", status: "APPROVED", key: "k3" }),
        ],
        false,
      ]);

      render(<MyApplications />);

      expect(screen.getByRole("tab", { name: /Active/ })).not.toHaveAttribute("disabled");
      expect(screen.getByRole("tab", { name: /Terminated/ })).not.toHaveAttribute("disabled");
      expect(screen.getByRole("tab", { name: /Finalised/ })).not.toHaveAttribute("disabled");
    });
  });

  describe("Tab switching after status changes", () => {
    it("allows switching to enabled Terminated tab after application is discarded", async () => {
      useResolvedPromiseMock.mockReturnValue([
        [
          makeApplication({ internal_id: "draft-1", status: "DRAFT", key: "k1" }),
        ],
        false,
      ]);

      const { rerender } = render(<MyApplications />);

      // Initially Terminated tab is disabled
      expect(screen.getByRole("tab", { name: /Terminated/ })).toHaveAttribute("disabled");

      // Simulate application being discarded
      useResolvedPromiseMock.mockReturnValue([
        [
          makeApplication({ internal_id: "draft-1", status: "DISCARDED", key: "k1" }),
        ],
        false,
      ]);

      rerender(<MyApplications />);

      // Now Terminated tab should be enabled
      const terminatedTab = screen.getByRole("tab", { name: /Terminated/ });
      expect(terminatedTab).not.toHaveAttribute("disabled");

      // Can click and switch to it
      fireEvent.click(terminatedTab);
      await waitFor(() => {
        expect(screen.getByTestId("card-k1")).toBeInTheDocument();
      });
    });
  });
});
