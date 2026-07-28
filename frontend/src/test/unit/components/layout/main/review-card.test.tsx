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
        />,
      );

      expect(screen.getByText("Initial Assessment (v3)")).toBeInTheDocument();
    });

    it("displays status chip", () => {
      render(
        <ReviewCard
          process={makeProcess()}
          application={makeApplication({ status: "UNDER_REVIEW" })}
        />,
      );

      expect(screen.getByText("Under Review")).toBeInTheDocument();
    });

    it("displays created and updated date chips with relative times", () => {
      render(
        <ReviewCard
          process={makeProcess()}
          application={makeApplication({ status: "SUBMITTED" })}
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
        />,
      );

      expect(screen.getByText("Jane Smith")).toBeInTheDocument();
    });

    it("displays unknown applicant when full name is missing", () => {
      render(
        <ReviewCard
          process={makeProcess()}
          application={makeApplication({ owner_fullname: "" })}
        />,
      );

      expect(screen.getByText("Unknown applicant")).toBeInTheDocument();
    });

    it("displays applicant email address with email icon", () => {
      render(
        <ReviewCard
          process={makeProcess()}
          application={makeApplication({ owner_email: "jane@example.com" })}
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

    it("has accessible tooltip on email box for click-to-copy hint", () => {
      render(
        <ReviewCard
          process={makeProcess()}
          application={makeApplication({ owner_email: "jane@example.com" })}
        />,
      );

      const emailBox = screen.getByText("jane@example.com").closest("div");
      expect(emailBox).toHaveAttribute("title", "Click to copy email address");
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
          application={makeApplication({ status: "SUBMITTED", submitted_at: submittedDate })}  />,
      );

      expect(screen.getByText(/Submitted.*ago/)).toBeInTheDocument();
    });

    it("displays 'pending' when application has not been submitted", () => {
      render(
        <ReviewCard
          process={makeProcess()}
          application={makeApplication({ status: "DRAFT", submitted_at: null })}  />,
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
        />,
      );

      expect(screen.getByRole("button", { name: "Files" })).toBeInTheDocument();
    });

    it("opens attachments dialog when files button is clicked", async () => {
      const application = makeApplication({ internal_id: "test-app-1" });

      render(
        <ReviewCard
          process={makeProcess()}
          application={application}
        />,
      );

      fireEvent.click(screen.getByRole("button", { name: "Files" }));

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
        />,
      );

      const downloadLink = screen.getByRole("link", { name: "Download application PDF" });
      expect(downloadLink).toHaveAttribute("href", `/d/${application.key}`);
      expect(downloadLink).toHaveAttribute("target", "_blank");
      expect(downloadLink).toHaveAttribute("rel", "noopener");
    });

    it("hides download button for non-downloadable statuses", () => {
      render(
        <ReviewCard
          process={makeProcess()}
          application={makeApplication({ status: "DRAFT" })}
        />,
      );

      expect(screen.queryByRole("link", { name: "Download application PDF" })).not.toBeInTheDocument();
    });

    it("shows PDF button with correct icon for downloadable applications", () => {
      render(
        <ReviewCard
          process={makeProcess()}
          application={makeApplication({ status: "UNDER_REVIEW", key: "app-key-789" })}
        />,
      );

      const downloadButton = screen.getByRole("button", { name: /PDF/i });
      expect(downloadButton).toBeInTheDocument();
      expect(downloadButton.closest("a")).toHaveAttribute("href", "/d/app-key-789");
    });
  });
});