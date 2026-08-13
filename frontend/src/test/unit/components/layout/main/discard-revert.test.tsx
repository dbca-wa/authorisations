import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApplicationCard } from "../../../../../components/layout/main/ApplicationCard";
import { ApiManager } from "../../../../../context/ApiManager";
import type { ApplicationStatus } from "../../../../../context/types/Application";
import { makeApplication, makeProcess } from "../../../fixtures";

const { showSnackbarMock } = vi.hoisted(() => ({
  showSnackbarMock: vi.fn(),
}));

vi.mock("../../../../../context/Hooks", async () => {
  const actual = await vi.importActual<typeof import("../../../../../context/Hooks")>("../../../../../context/Hooks");
  return {
    ...actual,
    useSnackbar: () => ({ showSnackbar: showSnackbarMock }),
  };
});

vi.mock("../../../../../context/ApiManager", async () => {
  const actual = await vi.importActual<typeof import("../../../../../context/ApiManager")>("../../../../../context/ApiManager");
  return {
    ...actual,
    ApiManager: {
      ...actual.ApiManager,
      discardApplication: vi.fn(),
      revertDiscardedApplication: vi.fn(),
    },
  };
});

/**
 * Tests for ApplicationCard discard and revert workflows.
 * Verifies that Discard (DRAFT only) and Revert (DISCARDED only) buttons
 * render conditionally and trigger appropriate API calls with callbacks.
 */
describe("ApplicationCard Discard and Revert Workflows", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("Discard button", () => {
    it("renders discard button for draft applications only", () => {
      render(
        <ApplicationCard
          process={makeProcess()}
          application={makeApplication({ status: "DRAFT" })}
          onStatusChanged={vi.fn()}
        />,
      );

      expect(screen.getByRole("button", { name: /Discard/ })).toBeInTheDocument();
    });

    it("does not render discard button for non-draft applications", () => {
      const nonDraftStatuses: ApplicationStatus[] = ["SUBMITTED", "UNDER_REVIEW", "UNDER_ASSESSMENT", "APPROVED"];

      nonDraftStatuses.forEach((status) => {
        const { unmount } = render(
          <ApplicationCard
            process={makeProcess()}
            application={makeApplication({ status })}
            onStatusChanged={vi.fn()}
          />,
        );

        expect(screen.queryByRole("button", { name: /Discard/ })).not.toBeInTheDocument();
        unmount();
      });
    });

    it("calls discardApplication API when discard button is clicked", async () => {
      const application = makeApplication({ key: "app-1", status: "DRAFT" });
      const discardedApp = { ...application, status: "DISCARDED" as const };

      vi.mocked(ApiManager.discardApplication).mockResolvedValue(discardedApp);
      const onStatusChanged = vi.fn();

      render(
        <ApplicationCard
          process={makeProcess()}
          application={application}
          onStatusChanged={onStatusChanged}
        />,
      );

      fireEvent.click(screen.getByRole("button", { name: /Discard/ }));

      await waitFor(() => {
        expect(ApiManager.discardApplication).toHaveBeenCalledWith("app-1");
      });
    });

    it("invokes onStatusChanged callback on successful discard", async () => {
      const application = makeApplication({ key: "app-1", status: "DRAFT" });
      const discardedApp = { ...application, status: "DISCARDED" as const };

      vi.mocked(ApiManager.discardApplication).mockResolvedValue(discardedApp);
      const onStatusChanged = vi.fn();

      render(
        <ApplicationCard
          process={makeProcess()}
          application={application}
          onStatusChanged={onStatusChanged}
        />,
      );

      fireEvent.click(screen.getByRole("button", { name: /Discard/ }));

      await waitFor(() => {
        expect(onStatusChanged).toHaveBeenCalledWith(discardedApp);
      });
    });

    it("shows success snackbar on discard success", async () => {
      const application = makeApplication({ key: "app-1", status: "DRAFT" });
      const discardedApp = { ...application, status: "DISCARDED" as const };

      vi.mocked(ApiManager.discardApplication).mockResolvedValue(discardedApp);

      render(
        <ApplicationCard
          process={makeProcess()}
          application={application}
          onStatusChanged={vi.fn()}
        />,
      );

      fireEvent.click(screen.getByRole("button", { name: /Discard/ }));

      await waitFor(() => {
        expect(showSnackbarMock).toHaveBeenCalledWith("Application discarded.", "info");
      });
    });

    it("shows error snackbar on discard failure", async () => {
      const application = makeApplication({ key: "app-1", status: "DRAFT" });

      vi.mocked(ApiManager.discardApplication).mockRejectedValue(new Error("Network error"));

      render(
        <ApplicationCard
          process={makeProcess()}
          application={application}
          onStatusChanged={vi.fn()}
        />,
      );

      fireEvent.click(screen.getByRole("button", { name: /Discard/ }));

      await waitFor(() => {
        expect(showSnackbarMock).toHaveBeenCalledWith(
          "Failed to discard application. Please try again later.",
          "error",
        );
      });
    });

    it("does not invoke callback on discard failure", async () => {
      const application = makeApplication({ key: "app-1", status: "DRAFT" });
      const onStatusChanged = vi.fn();

      vi.mocked(ApiManager.discardApplication).mockRejectedValue(new Error("Network error"));

      render(
        <ApplicationCard
          process={makeProcess()}
          application={application}
          onStatusChanged={onStatusChanged}
        />,
      );

      fireEvent.click(screen.getByRole("button", { name: /Discard/ }));

      await waitFor(() => {
        expect(onStatusChanged).not.toHaveBeenCalled();
      });
    });
  });

  describe("Revert button", () => {
    it("renders revert button for discarded applications only", () => {
      render(
        <ApplicationCard
          process={makeProcess()}
          application={makeApplication({ status: "DISCARDED" })}
          onStatusChanged={vi.fn()}
        />,
      );

      expect(screen.getByRole("button", { name: /Revert/ })).toBeInTheDocument();
    });

    it("does not render revert button for non-discarded applications", () => {
      const nonDiscardedStatuses: ApplicationStatus[] = ["DRAFT", "SUBMITTED", "UNDER_REVIEW", "APPROVED"];

      nonDiscardedStatuses.forEach((status) => {
        const { unmount } = render(
          <ApplicationCard
            process={makeProcess()}
            application={makeApplication({ status })}
            onStatusChanged={vi.fn()}
          />,
        );

        expect(screen.queryByRole("button", { name: "Revert" })).not.toBeInTheDocument();
        unmount();
      });
    });

    it("calls revertDiscardedApplication API when revert button is clicked", async () => {
      const application = makeApplication({ key: "app-2", status: "DISCARDED" });
      const revertedApp = { ...application, status: "DRAFT" as const };

      vi.mocked(ApiManager.revertDiscardedApplication).mockResolvedValue(revertedApp);
      const onStatusChanged = vi.fn();

      render(
        <ApplicationCard
          process={makeProcess()}
          application={application}
          onStatusChanged={onStatusChanged}
        />,
      );

      fireEvent.click(screen.getByRole("button", { name: /Revert/ }));

      await waitFor(() => {
        expect(ApiManager.revertDiscardedApplication).toHaveBeenCalledWith("app-2");
      });
    });

    it("invokes onStatusChanged callback on successful revert", async () => {
      const application = makeApplication({ key: "app-2", status: "DISCARDED" });
      const revertedApp = { ...application, status: "DRAFT" as const };

      vi.mocked(ApiManager.revertDiscardedApplication).mockResolvedValue(revertedApp);
      const onStatusChanged = vi.fn();

      render(
        <ApplicationCard
          process={makeProcess()}
          application={application}
          onStatusChanged={onStatusChanged}
        />,
      );

      fireEvent.click(screen.getByRole("button", { name: /Revert/ }));

      await waitFor(() => {
        expect(onStatusChanged).toHaveBeenCalledWith(revertedApp);
      });
    });

    it("shows success snackbar on revert success", async () => {
      const application = makeApplication({ key: "app-2", status: "DISCARDED" });
      const revertedApp = { ...application, status: "DRAFT" as const };

      vi.mocked(ApiManager.revertDiscardedApplication).mockResolvedValue(revertedApp);

      render(
        <ApplicationCard
          process={makeProcess()}
          application={application}
          onStatusChanged={vi.fn()}
        />,
      );

      fireEvent.click(screen.getByRole("button", { name: /Revert/ }));

      await waitFor(() => {
        expect(showSnackbarMock).toHaveBeenCalledWith("Application reverted to draft.", "info");
      });
    });

    it("shows error snackbar on revert failure", async () => {
      const application = makeApplication({ key: "app-2", status: "DISCARDED" });

      vi.mocked(ApiManager.revertDiscardedApplication).mockRejectedValue(new Error("Network error"));

      render(
        <ApplicationCard
          process={makeProcess()}
          application={application}
          onStatusChanged={vi.fn()}
        />,
      );

      fireEvent.click(screen.getByRole("button", { name: /Revert/ }));

      await waitFor(() => {
        expect(showSnackbarMock).toHaveBeenCalledWith(
          "Failed to revert application. Please try again later.",
          "error",
        );
      });
    });

    it("does not invoke callback on revert failure", async () => {
      const application = makeApplication({ key: "app-2", status: "DISCARDED" });
      const onStatusChanged = vi.fn();

      vi.mocked(ApiManager.revertDiscardedApplication).mockRejectedValue(new Error("Network error"));

      render(
        <ApplicationCard
          process={makeProcess()}
          application={application}
          onStatusChanged={onStatusChanged}
        />,
      );

      fireEvent.click(screen.getByRole("button", { name: /Revert/ }));

      await waitFor(() => {
        expect(onStatusChanged).not.toHaveBeenCalled();
      });
    });
  });
});
