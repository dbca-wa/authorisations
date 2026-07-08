import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AssessmentCard } from "../../../../../components/layout/main/AssessmentCard";
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


describe("AssessmentCard", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.mocked(ApiManagerModule.ApiManager.getApplicationAttachments).mockResolvedValue([]);
  });

  it("renders identifiers and process metadata", () => {
    render(
      <AssessmentCard
        process={makeProcess({ name: "Section 40" })}
        application={makeApplication({ internal_id: "s40-new-1/26-05", status: "SUBMITTED" })}
      />,
    );

    expect(screen.getByText("s40-new-1/26-05")).toBeInTheDocument();
    expect(screen.getByText("Section 40")).toBeInTheDocument();
    expect(screen.getByText("New application (v1)")).toBeInTheDocument();
  });

  it("displays the files button", () => {
    render(
      <AssessmentCard
        process={makeProcess()}
        application={makeApplication()}
      />,
    );

    expect(screen.getByRole("button", { name: "Files" })).toBeInTheDocument();
  });

  it("opens attachments dialog when files button is clicked", async () => {
    const application = makeApplication({ internal_id: "test-app-1" });

    render(
      <AssessmentCard
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
      <AssessmentCard
        process={makeProcess()}
        application={application}
      />,
    );

    const downloadLink = screen.getByRole("link", { name: "Download application PDF" });
    expect(downloadLink).toHaveAttribute("href", `/d/${application.key}`);
  });

  it("hides download button for non-downloadable statuses", () => {
    render(
      <AssessmentCard
        process={makeProcess()}
        application={makeApplication({ status: "DRAFT" })}
      />,
    );

    expect(screen.queryByRole("link", { name: "Download application PDF" })).not.toBeInTheDocument();
  });
});
