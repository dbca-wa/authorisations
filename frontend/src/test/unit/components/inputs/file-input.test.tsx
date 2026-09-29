import { act, fireEvent, screen, waitFor } from "@testing-library/react";
import React from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { FileInput } from "../../../../components/inputs/file";
import { ERROR_MSG } from "../../../../context/Constants";
import { makeQuestion, renderWithForm } from "./helpers";

const useDropzoneMock = vi.fn();
const showSnackbarMock = vi.fn();
const openFileDialogMock = vi.fn();
const uploadAttachmentMock = vi.fn();
let lastDropzoneOptions: Record<string, unknown> = {};
let dropzoneState = { isDragAccept: false, isDragReject: false };

const clientConfig = {
  app_version: "1.0.0",
  upload_mime_types: ["application/pdf", "image/png"],
  upload_max_size: 10 * 1024 * 1024,
};

vi.mock("react-dropzone", () => ({
  useDropzone: (...args: unknown[]) => useDropzoneMock(...args),
}));

vi.mock("../../../../context/ApiManager", () => ({
  ApiManager: {
    uploadAttachment: (...args: unknown[]) => uploadAttachmentMock(...args),
  },
}));

vi.mock("../../../../context/ConfigManager", () => ({
  ConfigManager: {
    get: () => clientConfig,
  },
}));

vi.mock("../../../../context/Hooks", () => ({
  useSnackbar: () => ({
    showSnackbar: showSnackbarMock,
  }),
}));

vi.mock("../../../../components/Common", () => ({
  FileAttachmentList: ({ attachments, onAttachmentDeleted }: {
    attachments: Array<{ key: string; name: string }>;
    onAttachmentDeleted: (key: string) => void;
  }) => (
    <div>
      <div data-testid="attachment-list">{attachments.map((item) => item.name).join(",")}</div>
      {attachments[0] && (
        <button type="button" onClick={() => onAttachmentDeleted(attachments[0].key)}>
          Delete first attachment
        </button>
      )}
    </div>
  ),
  HintButton: ({ hint }: { hint: string }) => <span>{`Hint: ${hint}`}</span>,
}));

const makeAttachment = (key: string, questionKey: string, name: string) => ({
  key,
  application_key: "app-1",
  question: questionKey,
  name,
  created_at: "2026-05-14T00:00:00Z",
  download_url: `/d/${key}`,
  size: 1024,
});

const renderFileInput = ({
  question,
  attachments,
  onAttachmentAdded = vi.fn(),
  onAttachmentDeleted = vi.fn(),
  onAttachmentUpdated = vi.fn(),
  defaultValues,
  onSubmit,
}: {
  question: ReturnType<typeof makeQuestion>;
  attachments: ReturnType<typeof makeAttachment>[];
  onAttachmentAdded?: (...args: unknown[]) => void;
  onAttachmentDeleted?: (...args: unknown[]) => void;
  onAttachmentUpdated?: (...args: unknown[]) => void;
  defaultValues?: Record<string, unknown>;
  onSubmit?: (values: Record<string, unknown>) => void;
}) => renderWithForm({
  defaultValues: defaultValues as never,
  onSubmit: onSubmit as never,
  ui: (
    <FileInput
      question={question}
      applicationKey="app-1"
      attachments={attachments}
      onAttachmentAdded={onAttachmentAdded as never}
      onAttachmentDeleted={onAttachmentDeleted as never}
      onAttachmentUpdated={onAttachmentUpdated as never}
    />
  ),
});

const getOnDrop = () => {
  const onDrop = lastDropzoneOptions.onDrop as ((accepted: File[], rejected: unknown[]) => Promise<void>) | undefined;
  expect(onDrop).toBeDefined();
  return onDrop;
};

const getDropzone = () => {
  const uploadButton = screen.getByRole("button", { name: "Select from computer" });
  const dropzone = uploadButton.closest(".dropzone");
  expect(dropzone).not.toBeNull();
  return dropzone as HTMLElement;
};


describe("FileInput", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    lastDropzoneOptions = {};
    dropzoneState = { isDragAccept: false, isDragReject: false };
    clientConfig.upload_mime_types = ["application/pdf", "image/png"];
    clientConfig.upload_max_size = 10 * 1024 * 1024;

    useDropzoneMock.mockImplementation((options: Record<string, unknown>) => {
      lastDropzoneOptions = options;
      return {
        getInputProps: () => ({}),
        getRootProps: (props: Record<string, unknown>) => props,
        open: openFileDialogMock,
        isDragAccept: dropzoneState.isDragAccept,
        isDragReject: dropzoneState.isDragReject,
      };
    });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("renders label, hint, helper text and upload call-to-action", () => {
    const question = makeQuestion({
      type: "file",
      label: "Upload files",
      config: { file_max_attachments: 2, hint: "Allowed evidence files" },
      description: "Attach evidence",
    });

    renderFileInput({
      question,
      attachments: [],
    });

    expect(screen.getByRole("heading", { name: /upload files/i })).toBeInTheDocument();
    expect(screen.getByText("Hint: Allowed evidence files")).toBeInTheDocument();
    expect(screen.getByText("Attach evidence")).toBeInTheDocument();
    expect(screen.getByText("Select from computer")).toBeInTheDocument();
    expect(screen.getByText(/Maximum file size limit is/i)).toBeInTheDocument();
  });

  it("shows attachment list and hides upload call-to-action once max=1 is reached", () => {
    const question = makeQuestion({
      type: "file",
      label: "Upload files",
      config: { file_max_attachments: 1 },
    });

    renderFileInput({
      question,
      attachments: [makeAttachment("att-1", question.key, "Evidence.pdf")],
    });

    expect(screen.queryByText("Select from computer")).not.toBeInTheDocument();
    expect(screen.getByTestId("attachment-list")).toHaveTextContent("Evidence.pdf");
  });

  it("shows and hides dropzone at expected attachment counts for max=3 and max=20", () => {
    const maxThreeQuestion = makeQuestion({
      type: "file",
      label: "Upload files",
      config: { file_max_attachments: 3 },
    });

    const maxTwentyQuestion = makeQuestion({
      type: "file",
      label: "Upload files",
      config: { file_max_attachments: 20 },
    });

    const attachmentsUpToThree = [
      [],
      [makeAttachment("att-1", maxThreeQuestion.key, "one.pdf")],
      [
        makeAttachment("att-1", maxThreeQuestion.key, "one.pdf"),
        makeAttachment("att-2", maxThreeQuestion.key, "two.pdf"),
      ],
    ];

    attachmentsUpToThree.forEach((attachments) => {
      const { unmount } = renderFileInput({
        question: maxThreeQuestion,
        attachments,
      });
      expect(screen.getByText("Select from computer")).toBeInTheDocument();
      unmount();
    });

    renderFileInput({
      question: maxThreeQuestion,
      attachments: [
        makeAttachment("att-1", maxThreeQuestion.key, "one.pdf"),
        makeAttachment("att-2", maxThreeQuestion.key, "two.pdf"),
        makeAttachment("att-3", maxThreeQuestion.key, "three.pdf"),
      ],
    });
    expect(screen.queryByText("Select from computer")).not.toBeInTheDocument();

    const { unmount } = renderFileInput({
      question: maxTwentyQuestion,
      attachments: Array.from({ length: 19 }, (_, index) =>
        makeAttachment(`att-${index + 1}`, maxTwentyQuestion.key, `file-${index + 1}.pdf`),
      ),
    });
    expect(screen.getByText("Select from computer")).toBeInTheDocument();
    unmount();

    renderFileInput({
      question: maxTwentyQuestion,
      attachments: Array.from({ length: 20 }, (_, index) =>
        makeAttachment(`att-${index + 1}`, maxTwentyQuestion.key, `file-${index + 1}.pdf`),
      ),
    });
    expect(screen.queryByText("Select from computer")).not.toBeInTheDocument();
  });

  it("forwards delete events from attachment list", () => {
    const onAttachmentDeleted = vi.fn();
    const question = makeQuestion({
      type: "file",
      label: "Upload files",
      config: { file_max_attachments: 2 },
    });

    renderFileInput({
      question,
      attachments: [makeAttachment("att-1", question.key, "Evidence.pdf")],
      onAttachmentDeleted,
    });

    fireEvent.click(screen.getByRole("button", { name: "Delete first attachment" }));
    expect(onAttachmentDeleted).toHaveBeenCalledWith("att-1", expect.any(Object));
  });

  it("opens the native file picker when the select button is clicked", () => {
    const question = makeQuestion({
      type: "file",
      label: "Upload files",
      config: { file_max_attachments: 1 },
    });

    renderFileInput({
      question,
      attachments: [],
    });

    fireEvent.click(screen.getByRole("button", { name: "Select from computer" }));
    expect(openFileDialogMock).toHaveBeenCalledTimes(1);
  });

  it("uploads a valid file, reports success, and invokes attachment callback", async () => {
    vi.useFakeTimers();
    const onAttachmentAdded = vi.fn();
    const question = makeQuestion({
      type: "file",
      label: "Upload files",
      config: { file_max_attachments: 3 },
    });

    const uploadedAttachment = makeAttachment("new-attachment-key", question.key, "evidence.pdf");

    uploadAttachmentMock.mockImplementation(async ({ callback }: { callback?: (event: { progress?: number }) => void }) => {
      callback?.({ progress: 0.4 });
      return uploadedAttachment;
    });

    renderFileInput({
      question,
      attachments: [],
      onAttachmentAdded,
    });

    const onDrop = getOnDrop();

    await act(async () => {
      await onDrop?.([
        new File(["dummy-pdf-content"], "evidence.pdf", { type: "application/pdf" }),
      ], []);
    });

    expect(uploadAttachmentMock).toHaveBeenCalledTimes(1);
    expect(onAttachmentAdded).toHaveBeenCalledWith(uploadedAttachment, expect.any(Object));
    expect(showSnackbarMock).toHaveBeenCalledWith("File has been uploaded", "success");
    expect(screen.getByText('Uploading "evidence.pdf"...')).toBeInTheDocument();

    act(() => {
      vi.advanceTimersByTime(3000);
    });

    expect(screen.queryByText('Uploading "evidence.pdf"...')).not.toBeInTheDocument();
    vi.useRealTimers();
  });

  it("shows API validation error message and does not invoke add callback", async () => {
    const onAttachmentAdded = vi.fn();
    const question = makeQuestion({
      type: "file",
      label: "Upload files",
      config: { file_max_attachments: 3 },
    });

    uploadAttachmentMock.mockRejectedValue({
      message: "Upload failed",
      response: {
        data: {
          file: "Server-side file validation failed.",
        },
      },
    });

    renderFileInput({
      question,
      attachments: [],
      onAttachmentAdded,
    });

    const onDrop = getOnDrop();

    await act(async () => {
      await onDrop?.([
        new File(["dummy-pdf-content"], "evidence.pdf", { type: "application/pdf" }),
      ], []);
    });

    expect(showSnackbarMock).toHaveBeenCalledWith(
      "Failed to upload: Server-side file validation failed.",
      "error",
    );
    expect(onAttachmentAdded).not.toHaveBeenCalled();
  });

  it("shows a validation snackbar when dropzone rejects dropped files", async () => {
    vi.useFakeTimers();
    const question = makeQuestion({
      type: "file",
      label: "Upload files",
      config: { file_max_attachments: 1 },
    });

    renderFileInput({
      question,
      attachments: [],
    });

    const onDrop = getOnDrop();

    await act(async () => {
      await onDrop?.([], [{ errors: [{ message: "Rejected" }] }]);
    });

    expect(showSnackbarMock).toHaveBeenCalledWith(
      "Invalid file type, please ensure it meets the requirements.",
      "error",
    );
    expect(screen.getByTestId("BlockIcon")).toBeInTheDocument();

    act(() => {
      vi.advanceTimersByTime(3000);
    });

    expect(screen.queryByTestId("BlockIcon")).not.toBeInTheDocument();
    vi.useRealTimers();
  });

  it("renders accept and reject drag states from dropzone", () => {
    const question = makeQuestion({ type: "file", label: "Upload files" });

    dropzoneState = { isDragAccept: true, isDragReject: false };
    const { unmount } = renderFileInput({ question, attachments: [] });

    expect(screen.getByTestId("CloudUploadIcon")).toBeInTheDocument();
    expect(getDropzone().className).toContain("border-green-500");
    unmount();

    dropzoneState = { isDragAccept: false, isDragReject: true };
    renderFileInput({ question, attachments: [] });

    expect(screen.getByTestId("BlockIcon")).toBeInTheDocument();
    expect(getDropzone().className).toContain("border-red-500");
  });

  it("resets post-drop rejection styling back to default on drag leave", () => {
    const question = makeQuestion({ type: "file", label: "Upload files" });

    renderFileInput({ question, attachments: [] });

    const onDropRejected = lastDropzoneOptions.onDropRejected as (() => void) | undefined;
    const onDragLeave = lastDropzoneOptions.onDragLeave as (() => void) | undefined;
    expect(onDropRejected).toBeDefined();
    expect(onDragLeave).toBeDefined();

    act(() => {
      onDropRejected?.();
    });

    expect(screen.getByTestId("BlockIcon")).toBeInTheDocument();

    act(() => {
      onDragLeave?.();
    });

    expect(screen.queryByTestId("BlockIcon")).not.toBeInTheDocument();
    expect(getDropzone().className).toContain("border-gray-400");
  });

  it("uses configured mime-types and validates file size with dropzone validator", () => {
    clientConfig.upload_mime_types = [
      "application/pdf",
      "image/png",
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ];
    clientConfig.upload_max_size = 1024;

    const question = makeQuestion({ type: "file", label: "Upload files" });
    renderFileInput({ question, attachments: [] });

    expect(lastDropzoneOptions.accept).toEqual({
      "application/pdf": [],
      "image/png": [],
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [],
    });

    const validator = lastDropzoneOptions.validator as ((file: File) => null | { code: string; message: string }) | undefined;
    expect(validator).toBeDefined();

    const oversizedFile = new File([new Uint8Array(2048)], "oversized.pdf", { type: "application/pdf" });
    const validFile = new File([new Uint8Array(512)], "valid.pdf", { type: "application/pdf" });

    expect(validator?.(oversizedFile)).toEqual({ code: "file-too-large", message: "File is too large." });
    expect(validator?.(validFile)).toBeNull();
  });

  it("syncs field state on mismatch and logs a warning", async () => {
    const warnSpy = vi.spyOn(console, "warn").mockImplementation(() => undefined);
    const question = makeQuestion({ type: "file", label: "Upload files" });
    const attachments = [makeAttachment("att-1", question.key, "evidence.pdf")];

    renderFileInput({
      question,
      attachments,
      defaultValues: {
        [question.key]: ["stale-key"],
      },
    });

    await waitFor(() => {
      expect(warnSpy).toHaveBeenCalled();
    });

    expect(warnSpy).toHaveBeenCalledWith(
      expect.stringContaining("Field value does not match the given attachments"),
      expect.objectContaining({ value: ["stale-key"], attachments: ["att-1"] }),
    );
    warnSpy.mockRestore();
  });

  it("logs sync warnings when attachments are removed and then cleared", async () => {
    const question = makeQuestion({ type: "file", label: "Upload files" });
    const warnSpy = vi.spyOn(console, "warn").mockImplementation(() => undefined);

    const Host = () => {
      const [attachments, setAttachments] = React.useState([
        makeAttachment("att-1", question.key, "one.pdf"),
        makeAttachment("att-2", question.key, "two.pdf"),
      ]);

      return (
        <>
          <button type="button" onClick={() => setAttachments((prev) => prev.slice(1))}>Remove first</button>
          <button type="button" onClick={() => setAttachments([])}>Clear all</button>
          <FileInput
            question={question}
            applicationKey="app-1"
            attachments={attachments}
            onAttachmentAdded={vi.fn()}
            onAttachmentDeleted={vi.fn()}
            onAttachmentUpdated={vi.fn()}
          />
        </>
      );
    };

    renderWithForm({
      ui: <Host />,
      defaultValues: {
        [question.key]: ["stale-key"],
      } as never,
    });

    fireEvent.click(screen.getByRole("button", { name: "Remove first" }));

    await waitFor(() => {
      expect(warnSpy).toHaveBeenCalledWith(
        expect.stringContaining("Field value does not match the given attachments"),
        expect.objectContaining({ attachments: ["att-2"] }),
      );
    });

    fireEvent.click(screen.getByRole("button", { name: "Clear all" }));

    await waitFor(() => {
      expect(warnSpy).toHaveBeenCalledWith(
        expect.stringContaining("Field value does not match the given attachments"),
        expect.objectContaining({ attachments: [] }),
      );
    });

    warnSpy.mockRestore();
  });

  it("shows required error in Alert when no files are attached", async () => {
    const question = makeQuestion({
      type: "file",
      label: "Required file",
      is_required: true,
    });

    renderFileInput({
      question,
      attachments: [],
    });

    fireEvent.click(screen.getByRole("button", { name: "Submit" }));

    await waitFor(() => {
      const alert = screen.getByRole("alert");
      expect(alert).toBeInTheDocument();
      expect(alert).toHaveTextContent(ERROR_MSG.required);
    });
  });

  it("cleans up pending reset timers on unmount", async () => {
    vi.useFakeTimers();
    const clearTimeoutSpy = vi.spyOn(window, "clearTimeout");
    const question = makeQuestion({ type: "file", label: "Upload files" });

    const { unmount } = renderFileInput({ question, attachments: [] });
    const onDropRejected = lastDropzoneOptions.onDropRejected as (() => void) | undefined;
    expect(onDropRejected).toBeDefined();

    act(() => {
      onDropRejected?.();
    });

    unmount();
    expect(clearTimeoutSpy).toHaveBeenCalled();

    clearTimeoutSpy.mockRestore();
    vi.useRealTimers();
  });
});
