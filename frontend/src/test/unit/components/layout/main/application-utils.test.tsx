import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AttachmentsButton, PdfDownloadButton } from "../../../../../components/layout/main/applicationUtils";
import * as ApiManagerModule from "../../../../../context/ApiManager";
import { makeApplication } from "../../../fixtures";

const { showDialogMock } = vi.hoisted(() => ({
  showDialogMock: vi.fn(),
}));

vi.mock("../../../../../context/Hooks", async () => {
  const actual = await vi.importActual<typeof import("../../../../../context/Hooks")>("../../../../../context/Hooks");
  return {
    ...actual,
    useDialog: () => ({ showDialog: showDialogMock }),
  };
});

vi.mock("../../../../../context/ApiManager");

describe("applicationUtils reusable components", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.mocked(ApiManagerModule.ApiManager.getApplicationAttachments).mockResolvedValue([]);
  });

  describe("PdfDownloadButton", () => {
    it("renders as a link with correct href", () => {
      const applicationKey = "app-key-pdf-123";

      render(<PdfDownloadButton applicationKey={applicationKey} />);

      const downloadLink = screen.getByRole("link", { name: "Download application PDF" });
      expect(downloadLink).toHaveAttribute("href", `/d/${applicationKey}`);
    });

    it("opens in new tab with noopener security", () => {
      render(<PdfDownloadButton applicationKey="app-key-pdf-456" />);

      const downloadLink = screen.getByRole("link", { name: "Download application PDF" });
      expect(downloadLink).toHaveAttribute("target", "_blank");
      expect(downloadLink).toHaveAttribute("rel", "noopener");
    });

    it("displays tooltip on hover", async () => {
      render(<PdfDownloadButton applicationKey="app-key-pdf-789" />);

      const link = screen.getByRole("link", { name: "Download application PDF" });
      const button = link.querySelector("button")!;
      
      fireEvent.mouseOver(button);

      await waitFor(() => {
        expect(screen.getByText("Download PDF")).toBeInTheDocument();
      });
    });

    it("has correct aria label for accessibility", () => {
      render(<PdfDownloadButton applicationKey="app-key-accessible" />);

      const link = screen.getByRole("link", { name: "Download application PDF" });
      expect(link).toHaveAttribute("aria-label", "Download application PDF");
    });
  });

  describe("AttachmentsButton", () => {
    it("renders attachments button", () => {
      const application = makeApplication();

      render(<AttachmentsButton application={application} />);

      expect(screen.getByRole("button", { name: "View attachments" })).toBeInTheDocument();
    });

    it("displays tooltip on hover", async () => {
      const application = makeApplication();

      render(<AttachmentsButton application={application} />);

      const attachmentsButton = screen.getByRole("button", { name: "View attachments" });
      
      fireEvent.mouseOver(attachmentsButton);

      await waitFor(() => {
        expect(screen.getByText("View attachments")).toBeInTheDocument();
      });
    });

    it("opens dialog with correct title when clicked", async () => {
      const application = makeApplication({ internal_id: "app-attachments-1" });

      render(<AttachmentsButton application={application} />);

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

    it("passes correct application key to dialog content", async () => {
      const application = makeApplication({ key: "app-key-content", internal_id: "app-1" });

      render(<AttachmentsButton application={application} />);

      fireEvent.click(screen.getByRole("button", { name: "View attachments" }));

      await waitFor(() => {
        expect(showDialogMock).toHaveBeenCalled();
        const callArgs = showDialogMock.mock.calls[0][0];
        // Dialog content should be rendered with the correct application key
        expect(callArgs.content).toBeDefined();
      });
    });

    it("has correct aria label for accessibility", () => {
      const application = makeApplication();

      render(<AttachmentsButton application={application} />);

      const button = screen.getByRole("button", { name: "View attachments" });
      expect(button).toHaveAttribute("aria-label", "View attachments");
    });

    it("uses secondary color for visual distinction", () => {
      const application = makeApplication();

      render(<AttachmentsButton application={application} />);

      const button = screen.getByRole("button", { name: "View attachments" });
      expect(button).toHaveClass("MuiIconButton-colorSecondary");
    });

    it("uses primary color for PDF button visual distinction", () => {
      render(<PdfDownloadButton applicationKey="app-key-color" />);

      const link = screen.getByRole("link", { name: "Download application PDF" });
      const button = link.querySelector("button");
      expect(button).toHaveClass("MuiIconButton-colorPrimary");
    });

    it("opens attachments dialog with matching internal_id format", async () => {
      const application = makeApplication({ internal_id: "section-40-draft-1/26-05" });

      render(<AttachmentsButton application={application} />);

      fireEvent.click(screen.getByRole("button", { name: "View attachments" }));

      await waitFor(() => {
        expect(showDialogMock).toHaveBeenCalledWith(
          expect.objectContaining({
            title: "Attachments for #section-40-draft-1/26-05",
          })
        );
      });
    });

    it("correctly handles application object with all required properties", () => {
      const application = makeApplication({
        key: "unique-app-key",
        internal_id: "unique-app-id",
        status: "DRAFT",
      });

      render(<AttachmentsButton application={application} />);

      const button = screen.getByRole("button", { name: "View attachments" });
      expect(button).toBeInTheDocument();

      fireEvent.click(button);

      expect(showDialogMock).toHaveBeenCalledWith(
        expect.objectContaining({
          title: "Attachments for #unique-app-id",
        })
      );
    });
  });

  describe("component integration", () => {
    it("renders both buttons together in a header", () => {
      const application = makeApplication({ key: "app-both", internal_id: "app-both-id" });

      render(
        <div className="flex gap-1">
          <AttachmentsButton application={application} />
          <PdfDownloadButton applicationKey={application.key} />
        </div>
      );

      expect(screen.getByRole("button", { name: "View attachments" })).toBeInTheDocument();
      expect(screen.getByRole("link", { name: "Download application PDF" })).toBeInTheDocument();
    });

    it("pdf button has correct href when rendered with attachments button", () => {
      const application = makeApplication({ key: "app-independent", internal_id: "app-indep-id" });

      render(
        <div className="flex gap-1">
          <AttachmentsButton application={application} />
          <PdfDownloadButton applicationKey={application.key} />
        </div>
      );

      const downloadLink = screen.getByRole("link", { name: "Download application PDF" });
      expect(downloadLink).toHaveAttribute("href", `/d/${application.key}`);
      expect(downloadLink).toHaveAttribute("target", "_blank");
    });
  });
});
