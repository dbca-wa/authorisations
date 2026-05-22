import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { IApplicationAttachment } from "../../../context/types/Application";

const {
  apiMocks,
  hideDialogMock,
  showDialogMock,
  showSnackbarMock,
  iconMock,
} = vi.hoisted(() => ({
  apiMocks: {
    deleteAttachment: vi.fn(),
    renameAttachment: vi.fn(),
  },
  hideDialogMock: vi.fn(),
  showDialogMock: vi.fn(),
  showSnackbarMock: vi.fn(),
  iconMock: vi.fn(() => <span data-testid="file-icon">icon</span>),
}));

vi.mock("../../../context/ApiManager", () => ({
  ApiManager: apiMocks,
}));

vi.mock("../../../context/Hooks", async () => {
  const actual = await vi.importActual<typeof import("../../../context/Hooks")>("../../../context/Hooks");
  return {
    ...actual,
    useDialog: () => ({ showDialog: showDialogMock, hideDialog: hideDialogMock }),
    useSnackbar: () => ({ showSnackbar: showSnackbarMock }),
  };
});

vi.mock("../../../context/Utils", async () => {
  const actual = await vi.importActual<typeof import("../../../context/Utils")>("../../../context/Utils");
  return {
    ...actual,
    getIconFromFilename: (...args: unknown[]) => iconMock(...args),
  };
});

import { FileAttachmentList } from "../../../components/Common";

const makeAttachment = (overrides: Partial<IApplicationAttachment> = {}): IApplicationAttachment => ({
  key: "att-1",
  application_key: "app-key-1",
  question: "0-0",
  name: "report.pdf",
  created_at: "2026-01-01T00:00:00Z",
  download_url: "/d/app-key-1/att-1",
  ...overrides,
});

describe("FileAttachmentList", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders attachments and hides edit actions when canEdit is false", () => {
    const attachment = makeAttachment();

    render(<FileAttachmentList attachments={[attachment]} canEdit={false} />);

    expect(screen.getByText("report.pdf")).toBeInTheDocument();
    expect(screen.getByRole("link")).toHaveAttribute("href", "/d/app-key-1/att-1");
    expect(screen.queryByTitle("Delete: report.pdf")).not.toBeInTheDocument();
    expect(screen.queryByTitle("Rename: report.pdf")).not.toBeInTheDocument();
    expect(iconMock).toHaveBeenCalledWith("report.pdf");
  });

  it("deletes an attachment after confirmation and notifies parent", async () => {
    const attachment = makeAttachment();
    const onAttachmentDeleted = vi.fn();
    apiMocks.deleteAttachment.mockResolvedValue(undefined);

    render(
      <FileAttachmentList
        attachments={[attachment]}
        canEdit={true}
        onAttachmentDeleted={onAttachmentDeleted}
      />,
    );

    fireEvent.click(screen.getByTitle("Delete: report.pdf"));

    expect(showDialogMock).toHaveBeenCalledWith(expect.objectContaining({ title: "Confirm Deletion" }));
    const dialogOptions = showDialogMock.mock.calls[0][0];

    render(<>{dialogOptions.actions}</>);
    fireEvent.click(screen.getByRole("button", { name: "Delete" }));

    await waitFor(() => {
      expect(apiMocks.deleteAttachment).toHaveBeenCalledWith("att-1");
      expect(onAttachmentDeleted).toHaveBeenCalledWith("att-1");
      expect(showSnackbarMock).toHaveBeenCalledWith("File has been deleted", "success");
      expect(hideDialogMock).toHaveBeenCalled();
    });
  });

  it("shows an error snackbar when delete request fails", async () => {
    const attachment = makeAttachment();
    apiMocks.deleteAttachment.mockRejectedValue({
      response: { data: { detail: "Not permitted" } },
    });

    render(<FileAttachmentList attachments={[attachment]} canEdit={true} />);

    fireEvent.click(screen.getByTitle("Delete: report.pdf"));
    const dialogOptions = showDialogMock.mock.calls[0][0];

    render(<>{dialogOptions.actions}</>);
    fireEvent.click(screen.getByRole("button", { name: "Delete" }));

    await waitFor(() => {
      expect(showSnackbarMock).toHaveBeenCalledWith("Failed to delete file: Not permitted", "error");
    });
  });

  it("renames an attachment from dialog input and preserves extension", async () => {
    const attachment = makeAttachment({ name: "report-v1.pdf" });
    const updatedAttachment = makeAttachment({ name: "renamed.pdf" });
    const onAttachmentUpdated = vi.fn();
    apiMocks.renameAttachment.mockResolvedValue(updatedAttachment);

    render(
      <FileAttachmentList
        attachments={[attachment]}
        canEdit={true}
        onAttachmentUpdated={onAttachmentUpdated}
      />,
    );

    fireEvent.click(screen.getByTitle("Rename: report-v1.pdf"));

    expect(showDialogMock).toHaveBeenCalledWith(expect.objectContaining({ title: "Rename Attachment" }));
    const dialogOptions = showDialogMock.mock.calls[0][0];

    render(<>{dialogOptions.content}</>);
    const fileNameInput = screen.getByLabelText("File name");
    fireEvent.change(fileNameInput, { target: { value: "renamed" } });
    fireEvent.keyDown(fileNameInput, { key: "Enter" });

    await waitFor(() => {
      expect(apiMocks.renameAttachment).toHaveBeenCalledWith("att-1", "renamed.pdf");
      expect(onAttachmentUpdated).toHaveBeenCalledWith(updatedAttachment);
      expect(showSnackbarMock).toHaveBeenCalledWith("File has been renamed", "success");
      expect(hideDialogMock).toHaveBeenCalled();
    });
  });
});