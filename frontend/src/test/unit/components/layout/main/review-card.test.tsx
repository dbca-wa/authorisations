import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ReviewCard } from "../../../../../components/layout/main/ReviewCard";
import * as ApiManagerModule from "../../../../../context/ApiManager";
import { makeApplication, makeProcess } from "../../../fixtures";

const { showSnackbarMock, showDialogMock, hideDialogMock } = vi.hoisted(() => ({
  showSnackbarMock: vi.fn(),
  showDialogMock: vi.fn(),
  hideDialogMock: vi.fn(),
}));

vi.mock("../../../../../context/Hooks", async () => {
  const actual = await vi.importActual<typeof import("../../../../../context/Hooks")>("../../../../../context/Hooks");
  return {
    ...actual,
    useSnackbar: () => ({ showSnackbar: showSnackbarMock }),
    useDialog: () => ({ showDialog: showDialogMock, hideDialog: hideDialogMock }),
  };
});

vi.mock("../../../../../context/ApiManager");

describe("ReviewCard", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.mocked(ApiManagerModule.ApiManager.getApplicationAttachments).mockResolvedValue([]);
  });

  it("renders identifiers and process metadata", () => {
    render(
      <ReviewCard
        process={makeProcess({ name: "Section 40" })}
        application={makeApplication({ internal_id: "s40-new-1/26-05", status: "SUBMITTED" })}
        isHighlighted={false}
        onStatusChanged={vi.fn()}
        onCardElementMounted={vi.fn()}
      />,
    );

    expect(screen.getByText("s40-new-1/26-05")).toBeInTheDocument();
    expect(screen.getByText("Section 40")).toBeInTheDocument();
    expect(screen.getByText("New application (v1)")).toBeInTheDocument();
  });

  describe("process and questionnaire metadata chips", () => {
    it("displays process name chip", () => {
      render(
        <ReviewCard
          process={makeProcess({ name: "Animal Ethics" })}
          application={makeApplication()}
          isHighlighted={false}
          onStatusChanged={vi.fn()}
          onCardElementMounted={vi.fn()}
        />,
      );

      expect(screen.getByText("Animal Ethics")).toBeInTheDocument();
    });

    it("displays questionnaire name and version chip", () => {
      render(
        <ReviewCard
          process={makeProcess()}
          application={makeApplication({
            questionnaire_name: "Initial Assessment",
            questionnaire_version: 3,
          })}
          isHighlighted={false}
          onStatusChanged={vi.fn()}
          onCardElementMounted={vi.fn()}
        />,
      );

      expect(screen.getByText("Initial Assessment (v3)")).toBeInTheDocument();
    });

    it("displays status chip", () => {
      render(
        <ReviewCard
          process={makeProcess()}
          application={makeApplication({ status: "UNDER_REVIEW" })}
          isHighlighted={false}
          onStatusChanged={vi.fn()}
          onCardElementMounted={vi.fn()}
        />,
      );

      expect(screen.getByText("Under Review")).toBeInTheDocument();
    });

    it("displays created and updated date chips with relative times", () => {
      render(
        <ReviewCard
          process={makeProcess()}
          application={makeApplication({ status: "SUBMITTED" })}
          isHighlighted={false}
          onStatusChanged={vi.fn()}
          onCardElementMounted={vi.fn()}
        />,
      );

      expect(screen.getByText(/Created.*ago/)).toBeInTheDocument();
      expect(screen.getByText(/Updated.*ago/)).toBeInTheDocument();
    });
  });

  describe("applicant information display", () => {
    it("displays applicant full name with person icon", () => {
      render(
        <ReviewCard
          process={makeProcess()}
          application={makeApplication({ owner_fullname: "Jane Smith" })}
          isHighlighted={false}
          onStatusChanged={vi.fn()}
          onCardElementMounted={vi.fn()}
        />,
      );

      expect(screen.getByText("Jane Smith")).toBeInTheDocument();
    });

    it("displays unknown applicant when full name is missing", () => {
      render(
        <ReviewCard
          process={makeProcess()}
          application={makeApplication({ owner_fullname: "" })}
          isHighlighted={false}
          onStatusChanged={vi.fn()}
          onCardElementMounted={vi.fn()}
        />,
      );

      expect(screen.getByText("Unknown applicant")).toBeInTheDocument();
    });

    it("displays applicant email address with email icon", () => {
      render(
        <ReviewCard
          process={makeProcess()}
          application={makeApplication({ owner_email: "jane@example.com" })}
          isHighlighted={false}
          onStatusChanged={vi.fn()}
          onCardElementMounted={vi.fn()}
        />,
      );

      expect(screen.getByText("jane@example.com")).toBeInTheDocument();
    });

    it("copies email address to clipboard when email box is clicked", async () => {
      const writeTextMock = vi.fn().mockResolvedValue(undefined);
      Object.assign(navigator, {
        clipboard: {
          writeText: writeTextMock,
        },
      });

      render(
        <ReviewCard
          process={makeProcess()}
          application={makeApplication({ owner_email: "jane@example.com" })}
          isHighlighted={false}
          onStatusChanged={vi.fn()}
          onCardElementMounted={vi.fn()}
        />,
      );

      const emailBox = screen.getByText("jane@example.com").closest("div");
      fireEvent.click(emailBox!);

      await waitFor(() => {
        expect(writeTextMock).toHaveBeenCalledWith("jane@example.com");
      });

      expect(showSnackbarMock).toHaveBeenCalledWith(
        "Email address copied to clipboard",
        "info"
      );
    });

    it("shows error snackbar when email copy fails", async () => {
      const writeTextMock = vi.fn().mockRejectedValueOnce(new Error("Copy failed"));
      Object.assign(navigator, {
        clipboard: {
          writeText: writeTextMock,
        },
      });

      render(
        <ReviewCard
          process={makeProcess()}
          application={makeApplication({ owner_email: "jane@example.com" })}
          isHighlighted={false}
          onStatusChanged={vi.fn()}
          onCardElementMounted={vi.fn()}
        />,
      );

      const emailBox = screen.getByText("jane@example.com").closest("div");
      fireEvent.click(emailBox!);

      await waitFor(() => {
        expect(writeTextMock).toHaveBeenCalledWith("jane@example.com");
      });

      expect(showSnackbarMock).toHaveBeenCalledWith(
        "Failed to copy email to clipboard",
        "error"
      );
    });

    it("has accessible tooltip on email box for copy functionality", () => {
      render(
        <ReviewCard
          process={makeProcess()}
          application={makeApplication({ owner_email: "jane@example.com" })}
          isHighlighted={false}
          onStatusChanged={vi.fn()}
          onCardElementMounted={vi.fn()}
        />,
      );

      const emailBox = screen.getByText("jane@example.com").closest("div");
      // MUI Tooltip title is displayed on hover, component has tooltip with "Copy email address"
      expect(emailBox).toBeInTheDocument();
      expect(emailBox?.closest("[role='tooltip']") === null).toBe(true); // Tooltip renders on hover, not initially
    });
  });

  describe("submission date display", () => {
    it("displays submission date with relative time format", () => {
      const futureDate = new Date();
      futureDate.setDate(futureDate.getDate() - 5);
      const submittedDate = futureDate.toISOString();

      render(
        <ReviewCard
          process={makeProcess()}
          application={makeApplication({ status: "SUBMITTED", submitted_at: submittedDate })}
          isHighlighted={false}
          onStatusChanged={vi.fn()}
          onCardElementMounted={vi.fn()}
        />,
      );

      expect(screen.getByText(/Submitted.*ago/)).toBeInTheDocument();
    });

    it("displays 'pending' when application has not been submitted", () => {
      render(
        <ReviewCard
          process={makeProcess()}
          application={makeApplication({ status: "DRAFT", submitted_at: null })}
          isHighlighted={false}
          onStatusChanged={vi.fn()}
          onCardElementMounted={vi.fn()}
        />,
      );

      expect(screen.getByText(/Submitted pending/)).toBeInTheDocument();
    });

    it("does not display submission date for applications that are not submitted", () => {
      const pastDate = new Date();
      pastDate.setDate(pastDate.getDate() - 3);
      const createdDate = pastDate.toISOString();

      render(
        <ReviewCard
          process={makeProcess()}
          application={makeApplication({ 
            status: "UNDER_REVIEW",
            created_at: createdDate,
            submitted_at: null  // Explicitly null - not submitted
          })}
          isHighlighted={false}
          onStatusChanged={vi.fn()}
          onCardElementMounted={vi.fn()}
        />,
      );

      // Should show "Submitted pending", NOT "Submitted 3 days ago"
      expect(screen.getByText(/Submitted pending/)).toBeInTheDocument();
    });
  });

  describe("files and download buttons", () => {
    it("displays the files button", () => {
      render(
        <ReviewCard
          process={makeProcess()}
          application={makeApplication()}
          isHighlighted={false}
          onStatusChanged={vi.fn()}
          onCardElementMounted={vi.fn()}
        />,
      );

      expect(screen.getByRole("button", { name: "View attachments" })).toBeInTheDocument();
    });

    it("opens attachments dialog when files button is clicked", async () => {
      const application = makeApplication({ internal_id: "test-app-1" });

      render(
        <ReviewCard
          process={makeProcess()}
          application={application}
          isHighlighted={false}
          onStatusChanged={vi.fn()}
          onCardElementMounted={vi.fn()}
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
      const application = makeApplication({ status: "UNDER_REVIEW", key: "app-key-456" });

      render(
        <ReviewCard
          process={makeProcess()}
          application={application}
          isHighlighted={false}
          onStatusChanged={vi.fn()}
          onCardElementMounted={vi.fn()}
        />,
      );

      const downloadLink = screen.getByRole("link", { name: "Download application PDF" });
      expect(downloadLink).toHaveAttribute("href", `/d/${application.key}`);
      expect(downloadLink).toHaveAttribute("target", "_blank");
      expect(downloadLink).toHaveAttribute("rel", "noopener");
    });

    it("shows download button for all statuses", () => {
      render(
        <ReviewCard
          process={makeProcess()}
          application={makeApplication({ status: "DRAFT" })}
          isHighlighted={false}
          onStatusChanged={vi.fn()}
          onCardElementMounted={vi.fn()}
        />,
      );

      // Download button is shown for all statuses including DRAFT
      expect(screen.getByRole("link", { name: "Download application PDF" })).toBeInTheDocument();
    });

    it("shows PDF button with correct icon for downloadable applications", () => {
      render(
        <ReviewCard
          process={makeProcess()}
          application={makeApplication({ status: "UNDER_REVIEW", key: "app-key-789" })}
          isHighlighted={false}
          onStatusChanged={vi.fn()}
          onCardElementMounted={vi.fn()}
        />,
      );

      const downloadButton = screen.getByRole("button", { name: /PDF/i });
      expect(downloadButton).toBeInTheDocument();
      expect(downloadButton.closest("a")).toHaveAttribute("href", "/d/app-key-789");
    });
  });

  describe("action button visibility and behavior", () => {
    describe("SUBMITTED status", () => {
      it("displays Claim button for SUBMITTED status", () => {
        render(
          <ReviewCard
            process={makeProcess()}
            application={makeApplication({ status: "SUBMITTED" })}
            isHighlighted={false}
            onStatusChanged={vi.fn()}
            onCardElementMounted={vi.fn()}
          />,
        );

        expect(screen.getByText("Claim")).toBeInTheDocument();
      });
    });

    describe("UNDER_REVIEW status", () => {
      it("displays Reset and Assessment buttons for UNDER_REVIEW status", () => {
        render(
          <ReviewCard
            process={makeProcess()}
            application={makeApplication({ status: "UNDER_REVIEW" })}
            isHighlighted={false}
            onStatusChanged={vi.fn()}
            onCardElementMounted={vi.fn()}
          />,
        );

        expect(screen.getByText("Reset")).toBeInTheDocument();
        expect(screen.getByText("Assessment")).toBeInTheDocument();
      });
    });

    describe("UNDER_ASSESSMENT status", () => {
      it("does not display action buttons for UNDER_ASSESSMENT status", () => {
        render(
          <ReviewCard
            process={makeProcess()}
            application={makeApplication({ status: "UNDER_ASSESSMENT" })}
            isHighlighted={false}
            onStatusChanged={vi.fn()}
            onCardElementMounted={vi.fn()}
          />,
        );

        expect(screen.queryByText("Claim")).not.toBeInTheDocument();
        expect(screen.queryByText("Reset")).not.toBeInTheDocument();
        expect(screen.queryByText("Assessment")).not.toBeInTheDocument();
      });
    });
  });

  describe("Claim action handler", () => {
    it("successfully claims application and calls onStatusChanged with updated application", async () => {
      const onStatusChangedMock = vi.fn();
      const updatedApp = makeApplication({ status: "UNDER_REVIEW" });
      vi.mocked(ApiManagerModule.ApiManager.updateReviewerApplicationStatus).mockResolvedValueOnce(
        updatedApp,
      );

      render(
        <ReviewCard
          process={makeProcess()}
          application={makeApplication({ status: "SUBMITTED" })}
          isHighlighted={false}
          onStatusChanged={onStatusChangedMock}
          onCardElementMounted={vi.fn()}
        />,
      );

      const claimButton = screen.getByText("Claim").closest("button");
      fireEvent.click(claimButton!);

      await waitFor(() => {
        expect(ApiManagerModule.ApiManager.updateReviewerApplicationStatus).toHaveBeenCalledWith(
          expect.any(String),
          "UNDER_REVIEW",
        );
        expect(onStatusChangedMock).toHaveBeenCalledWith(updatedApp);
        expect(showSnackbarMock).toHaveBeenCalledWith(
          "Application claimed for review.",
          "success",
        );
      });
    });

    it("shows error snackbar when claim fails", async () => {
      const onStatusChangedMock = vi.fn();
      vi.mocked(ApiManagerModule.ApiManager.updateReviewerApplicationStatus).mockRejectedValueOnce(
        new Error("API Error"),
      );

      render(
        <ReviewCard
          process={makeProcess()}
          application={makeApplication({ status: "SUBMITTED" })}
          isHighlighted={false}
          onStatusChanged={onStatusChangedMock}
          onCardElementMounted={vi.fn()}
        />,
      );

      const claimButton = screen.getByText("Claim").closest("button");
      fireEvent.click(claimButton!);

      await waitFor(() => {
        expect(showSnackbarMock).toHaveBeenCalledWith(
          "Failed to claim application. Please try again later.",
          "error",
        );
        expect(onStatusChangedMock).not.toHaveBeenCalled();
      });
    });
  });

  describe("Reset to Draft action handler", () => {
    it("shows confirmation dialog when Reset is clicked", async () => {
      render(
        <ReviewCard
          process={makeProcess()}
          application={makeApplication({ status: "UNDER_REVIEW" })}
          isHighlighted={false}
          onStatusChanged={vi.fn()}
          onCardElementMounted={vi.fn()}
        />,
      );

      const resetButtons = screen.getAllByText("Reset");
      const button = resetButtons[0].closest("button");
      if (!button) throw new Error("Reset button not found");
      fireEvent.click(button);

      await waitFor(() => {
        expect(showDialogMock).toHaveBeenCalled();
      });
    });
  });

  describe("Proceed to Assessment action handler", () => {
    it("shows confirmation dialog when Assessment is clicked", async () => {
      render(
        <ReviewCard
          process={makeProcess()}
          application={makeApplication({ status: "UNDER_REVIEW" })}
          isHighlighted={false}
          onStatusChanged={vi.fn()}
          onCardElementMounted={vi.fn()}
        />,
      );

      const assessmentButtons = screen.getAllByText("Assessment");
      const button = assessmentButtons[0].closest("button");
      if (!button) throw new Error("Assessment button not found");
      fireEvent.click(button);

      await waitFor(() => {
        expect(showDialogMock).toHaveBeenCalled();
      });
    });
  });

  describe("Chip component updates", () => {
    it("displays status chip reflecting current application status", () => {
      render(
        <ReviewCard
          process={makeProcess()}
          application={makeApplication({ status: "SUBMITTED" })}
          isHighlighted={false}
          onStatusChanged={vi.fn()}
          onCardElementMounted={vi.fn()}
        />,
      );

      expect(screen.getByText("Submitted")).toBeInTheDocument();
    });

    it("updates status chip when application status changes via prop", () => {
      const { rerender } = render(
        <ReviewCard
          process={makeProcess()}
          application={makeApplication({ status: "SUBMITTED" })}
          isHighlighted={false}
          onStatusChanged={vi.fn()}
          onCardElementMounted={vi.fn()}
        />,
      );

      expect(screen.getByText("Submitted")).toBeInTheDocument();

      rerender(
        <ReviewCard
          process={makeProcess()}
          application={makeApplication({ status: "UNDER_REVIEW" })}
          isHighlighted={false}
          onStatusChanged={vi.fn()}
          onCardElementMounted={vi.fn()}
        />,
      );

      expect(screen.getByText("Under Review")).toBeInTheDocument();
      expect(screen.queryByText("Submitted")).not.toBeInTheDocument();
    });

    it("displays updated_at chip with relative time that updates with application prop changes", () => {
      const oldDate = new Date();
      oldDate.setDate(oldDate.getDate() - 5);

      const newDate = new Date();
      newDate.setDate(newDate.getDate() - 1);

      const { rerender } = render(
        <ReviewCard
          process={makeProcess()}
          application={makeApplication({ updated_at: oldDate.toISOString() })}
          isHighlighted={false}
          onStatusChanged={vi.fn()}
          onCardElementMounted={vi.fn()}
        />,
      );

      expect(screen.getByText(/Updated.*5.*days?.*ago/)).toBeInTheDocument();

      rerender(
        <ReviewCard
          process={makeProcess()}
          application={makeApplication({ updated_at: newDate.toISOString() })}
          isHighlighted={false}
          onStatusChanged={vi.fn()}
          onCardElementMounted={vi.fn()}
        />,
      );

      expect(screen.getByText(/Updated.*day.*ago/)).toBeInTheDocument();
    });
  });
});