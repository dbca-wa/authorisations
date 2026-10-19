import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApplicationCard } from "../../../../../components/layout/main/ApplicationCard";
import * as UtilsModule from "../../../../../context/Utils";
import { makeApplication, makeProcess } from "../../../fixtures";

const { showSnackbarMock, showDialogMock } = vi.hoisted(() => ({
  showSnackbarMock: vi.fn(),
  showDialogMock: vi.fn(),
}));

vi.mock("../../../../../context/Hooks", async () => {
  const actual = await vi.importActual<typeof import("../../../../../context/Hooks")>("../../../../../context/Hooks");
  return {
    ...actual,
    useSnackbar: () => ({ showSnackbar: showSnackbarMock }),
    useDialog: () => ({ showDialog: showDialogMock }),
  };
});


describe("ApplicationCard", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders identifiers and process metadata", () => {
    render(
      <ApplicationCard
        process={makeProcess({ name: "Section 40" })}
        application={makeApplication({ internal_id: "s40-new-1/26-05", status: "SUBMITTED" })}
        onStatusChanged={vi.fn()}
      />,
    );

    expect(screen.getByText("s40-new-1/26-05")).toBeInTheDocument();
    expect(screen.getByText("Section 40")).toBeInTheDocument();
    expect(screen.getByText("New application (v1)")).toBeInTheDocument();
  });

  it("shows continue button for drafts", () => {
    render(
      <ApplicationCard
        process={makeProcess()}
        application={makeApplication({ status: "DRAFT" })}
        onStatusChanged={vi.fn()}
      />,
    );

    expect(screen.getByRole("button", { name: "Continue" })).toBeInTheDocument();
  });

  it("hides continue button for submitted or finalised applications", () => {
    render(
      <ApplicationCard
        process={makeProcess()}
        application={makeApplication({ status: "SUBMITTED" })}
        onStatusChanged={vi.fn()}
      />,
    );

    expect(screen.queryByRole("button", { name: "Continue" })).not.toBeInTheDocument();
  });

  it("opens form in new tab when continue is clicked", () => {
    const openNewTabSpy = vi.spyOn(UtilsModule, "openNewTab").mockImplementation(() => undefined);
    const application = makeApplication({ key: "app-key-1", status: "DRAFT" });

    render(
      <ApplicationCard
        process={makeProcess()}
        application={application}
        onStatusChanged={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Continue" }));

    expect(openNewTabSpy).toHaveBeenCalledWith("/a/app-key-1", "app-key-1");
  });

  describe("file and download buttons", () => {
    it("displays the attachments button", () => {
      render(
        <ApplicationCard
          process={makeProcess()}
          application={makeApplication()}
          onStatusChanged={vi.fn()}
        />,
      );

      expect(screen.getByRole("button", { name: "View attachments" })).toBeInTheDocument();
    });

    it("opens attachments dialog when attachments button is clicked", async () => {
      const application = makeApplication({ internal_id: "app-draft-1" });

      render(
        <ApplicationCard
          process={makeProcess()}
          application={application}
          onStatusChanged={vi.fn()}
        />,
      );

      fireEvent.click(screen.getByRole("button", { name: "View attachments" }));

      await waitFor(() => {
        expect(showDialogMock).toHaveBeenCalledWith(
          expect.objectContaining({
            title: `Attachments for #${application.internal_id}`,
            content: expect.anything(),
          })
        );
      });
    });

    it("shows download button for downloadable statuses", () => {
      const application = makeApplication({ status: "SUBMITTED", key: "app-key-123" });
      
      render(
        <ApplicationCard
          process={makeProcess()}
          application={application}
          onStatusChanged={vi.fn()}
        />,
      );

      const downloadLink = screen.getByRole("link", { name: "Download application PDF" });
      expect(downloadLink).toHaveAttribute("href", `/d/${application.key}`);
      expect(downloadLink).toHaveAttribute("target", "_blank");
      expect(downloadLink).toHaveAttribute("rel", "noopener");
    });

    it("shows download button for DRAFT status (preview purposes)", () => {
      const application = makeApplication({ status: "DRAFT", key: "app-key-draft" });
      render(
        <ApplicationCard
          process={makeProcess()}
          application={application}
          onStatusChanged={vi.fn()}
        />,
      );

      const downloadLink = screen.getByRole("link", { name: "Download application PDF" });
      expect(downloadLink).toHaveAttribute("href", `/d/${application.key}`);
      expect(downloadLink).toHaveAttribute("target", "_blank");
      expect(downloadLink).toHaveAttribute("rel", "noopener");
    });

    it("hides attachments button for DISCARDED (terminated) status", () => {
      render(
        <ApplicationCard
          process={makeProcess()}
          application={makeApplication({ status: "DISCARDED" })}
          onStatusChanged={vi.fn()}
        />,
      );

      expect(screen.queryByRole("button", { name: "View attachments" })).not.toBeInTheDocument();
    });

    it("hides attachments button for WITHDRAWN (terminated) status", () => {
      render(
        <ApplicationCard
          process={makeProcess()}
          application={makeApplication({ status: "WITHDRAWN" })}
          onStatusChanged={vi.fn()}
        />,
      );

      expect(screen.queryByRole("button", { name: "View attachments" })).not.toBeInTheDocument();
    });

    it("hides download button for DISCARDED (terminated) status", () => {
      render(
        <ApplicationCard
          process={makeProcess()}
          application={makeApplication({ status: "DISCARDED", key: "app-discarded" })}
          onStatusChanged={vi.fn()}
        />,
      );

      expect(screen.queryByRole("link", { name: "Download application PDF" })).not.toBeInTheDocument();
    });

    it("hides download button for WITHDRAWN (terminated) status", () => {
      render(
        <ApplicationCard
          process={makeProcess()}
          application={makeApplication({ status: "WITHDRAWN", key: "app-withdrawn" })}
          onStatusChanged={vi.fn()}
        />,
      );

      expect(screen.queryByRole("link", { name: "Download application PDF" })).not.toBeInTheDocument();
    });
  });

  it("does not display review button", () => {
    render(
      <ApplicationCard
        process={makeProcess()}
        application={makeApplication({ status: "SUBMITTED" })}
        onStatusChanged={vi.fn()}
      />,
    );

    expect(screen.queryByRole("button", { name: "Review" })).not.toBeInTheDocument();
  });

  describe("application status workflow stepper", () => {
    it("DRAFT displays stepper (not terminated alert)", () => {
      render(
        <ApplicationCard
          process={makeProcess()}
          application={makeApplication({ status: "DRAFT" })}
          onStatusChanged={vi.fn()}
        />,
      );

      expect(screen.queryByText("Application Terminated")).not.toBeInTheDocument();
      const steps = screen.getAllByRole("listitem");
      const muiSteps = steps.filter(el => el.className.includes("MuiStep"));
      expect(muiSteps).toHaveLength(5);
    });

    it("SUBMITTED displays stepper (not terminated alert)", () => {
      render(
        <ApplicationCard
          process={makeProcess()}
          application={makeApplication({ status: "SUBMITTED" })}
          onStatusChanged={vi.fn()}
        />,
      );

      expect(screen.queryByText("Application Terminated")).not.toBeInTheDocument();
      const steps = screen.getAllByRole("listitem");
      const muiSteps = steps.filter(el => el.className.includes("MuiStep"));
      expect(muiSteps).toHaveLength(5);
    });

    it("UNDER_REVIEW displays stepper (not terminated alert)", () => {
      render(
        <ApplicationCard
          process={makeProcess()}
          application={makeApplication({ status: "UNDER_REVIEW" })}
          onStatusChanged={vi.fn()}
        />,
      );

      expect(screen.queryByText("Application Terminated")).not.toBeInTheDocument();
      const steps = screen.getAllByRole("listitem");
      const muiSteps = steps.filter(el => el.className.includes("MuiStep"));
      expect(muiSteps).toHaveLength(5);
    });

    it("UNDER_ASSESSMENT displays stepper (not terminated alert)", () => {
      render(
        <ApplicationCard
          process={makeProcess()}
          application={makeApplication({ status: "UNDER_ASSESSMENT" })}
          onStatusChanged={vi.fn()}
        />,
      );

      expect(screen.queryByText("Application Terminated")).not.toBeInTheDocument();
      const steps = screen.getAllByRole("listitem");
      const muiSteps = steps.filter(el => el.className.includes("MuiStep"));
      expect(muiSteps).toHaveLength(5);
    });

    it("APPROVED displays stepper (not terminated alert)", () => {
      render(
        <ApplicationCard
          process={makeProcess()}
          application={makeApplication({ status: "APPROVED" })}
          onStatusChanged={vi.fn()}
        />,
      );

      expect(screen.queryByText("Application Terminated")).not.toBeInTheDocument();
      const steps = screen.getAllByRole("listitem");
      const muiSteps = steps.filter(el => el.className.includes("MuiStep"));
      expect(muiSteps).toHaveLength(5);
    });

    it("APPROVED_WITH_CONDITIONS displays stepper (not terminated alert)", () => {
      render(
        <ApplicationCard
          process={makeProcess()}
          application={makeApplication({ status: "APPROVED_WITH_CONDITIONS" })}
          onStatusChanged={vi.fn()}
        />,
      );

      expect(screen.queryByText("Application Terminated")).not.toBeInTheDocument();
      const steps = screen.getAllByRole("listitem");
      const muiSteps = steps.filter(el => el.className.includes("MuiStep"));
      expect(muiSteps).toHaveLength(5);
    });

    it("REJECTED displays stepper (not terminated alert)", () => {
      render(
        <ApplicationCard
          process={makeProcess()}
          application={makeApplication({ status: "REJECTED" })}
          onStatusChanged={vi.fn()}
        />,
      );

      expect(screen.queryByText("Application Terminated")).not.toBeInTheDocument();
      const steps = screen.getAllByRole("listitem");
      const muiSteps = steps.filter(el => el.className.includes("MuiStep"));
      expect(muiSteps).toHaveLength(5);
    });

    it("DEFERRED displays stepper (not terminated alert)", () => {
      render(
        <ApplicationCard
          process={makeProcess()}
          application={makeApplication({ status: "DEFERRED" })}
          onStatusChanged={vi.fn()}
        />,
      );

      expect(screen.queryByText("Application Terminated")).not.toBeInTheDocument();
      const steps = screen.getAllByRole("listitem");
      const muiSteps = steps.filter(el => el.className.includes("MuiStep"));
      expect(muiSteps).toHaveLength(5);
    });

    it("DISCARDED shows terminated alert (not stepper)", () => {
      render(
        <ApplicationCard
          process={makeProcess()}
          application={makeApplication({ status: "DISCARDED" })}
          onStatusChanged={vi.fn()}
        />,
      );

      expect(screen.getByText("Application Terminated")).toBeInTheDocument();
      const steps = screen.queryAllByRole("listitem").filter(el => el.className.includes("MuiStep"));
      expect(steps).toHaveLength(0);
    });

    it("WITHDRAWN shows terminated alert (not stepper)", () => {
      render(
        <ApplicationCard
          process={makeProcess()}
          application={makeApplication({ status: "WITHDRAWN" })}
          onStatusChanged={vi.fn()}
        />,
      );

      expect(screen.getByText("Application Terminated")).toBeInTheDocument();
      const steps = screen.queryAllByRole("listitem").filter(el => el.className.includes("MuiStep"));
      expect(steps).toHaveLength(0);
    });
  });
});
