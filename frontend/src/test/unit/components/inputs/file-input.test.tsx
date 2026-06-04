import { fireEvent, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { FileInput } from "../../../../components/inputs/file";
import { makeQuestion, renderWithForm } from "./helpers";

const useDropzoneMock = vi.fn();
const showSnackbarMock = vi.fn();
const openFileDialogMock = vi.fn();
let lastDropzoneOptions: Record<string, unknown> = {};

vi.mock("react-dropzone", () => ({
  useDropzone: (...args: unknown[]) => useDropzoneMock(...args),
}));

vi.mock("../../../../context/ConfigManager", () => ({
  ConfigManager: {
    get: () => ({
      upload_mime_types: ["application/pdf", "image/png"],
      upload_max_size: 10 * 1024 * 1024,
    }),
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
}));


describe("FileInput", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    lastDropzoneOptions = {};
    useDropzoneMock.mockReturnValue({
      getInputProps: () => ({}),
      getRootProps: (props: Record<string, unknown>) => props,
      open: openFileDialogMock,
      isDragAccept: false,
      isDragReject: false,
    });
    useDropzoneMock.mockImplementation((options: Record<string, unknown>) => {
      lastDropzoneOptions = options;
      return {
        getInputProps: () => ({}),
        getRootProps: (props: Record<string, unknown>) => props,
        open: openFileDialogMock,
        isDragAccept: false,
        isDragReject: false,
      };
    });
  });

  it("renders upload call-to-action when below max attachment count", () => {
    const question = makeQuestion({
      type: "file",
      label: "Upload files",
      file_max_attachments: 2,
      description: "Attach evidence",
    });

    renderWithForm({
      ui: (
        <FileInput
          question={question}
          applicationKey="app-1"
          attachments={[]}
          onAttachmentAdded={vi.fn()}
          onAttachmentDeleted={vi.fn()}
          onAttachmentUpdated={vi.fn()}
        />
      ),
    });

    expect(screen.getByText("Select from computer")).toBeInTheDocument();
    expect(screen.getByText(/Maximum file size limit is/i)).toBeInTheDocument();
  });

  it("hides upload call-to-action once attachment limit is reached", () => {
    const question = makeQuestion({
      type: "file",
      label: "Upload files",
      file_max_attachments: 1,
    });

    renderWithForm({
      ui: (
        <FileInput
          question={question}
          applicationKey="app-1"
          attachments={[
            {
              key: "att-1",
              application_key: "app-1",
              question: question.key,
              name: "Evidence.pdf",
              created_at: "2026-05-14T00:00:00Z",
              download_url: "/d/file",
            },
          ]}
          onAttachmentAdded={vi.fn()}
          onAttachmentDeleted={vi.fn()}
          onAttachmentUpdated={vi.fn()}
        />
      ),
    });

    expect(screen.queryByText("Select from computer")).not.toBeInTheDocument();
    expect(screen.getByTestId("attachment-list")).toHaveTextContent("Evidence.pdf");
  });

  it("forwards delete events from attachment list", () => {
    const onAttachmentDeleted = vi.fn();
    const question = makeQuestion({
      type: "file",
      label: "Upload files",
      file_max_attachments: 2,
    });

    renderWithForm({
      ui: (
        <FileInput
          question={question}
          applicationKey="app-1"
          attachments={[
            {
              key: "att-1",
              application_key: "app-1",
              question: question.key,
              name: "Evidence.pdf",
              created_at: "2026-05-14T00:00:00Z",
              download_url: "/d/file",
            },
          ]}
          onAttachmentAdded={vi.fn()}
          onAttachmentDeleted={onAttachmentDeleted}
          onAttachmentUpdated={vi.fn()}
        />
      ),
    });

    fireEvent.click(screen.getByRole("button", { name: "Delete first attachment" }));
    expect(onAttachmentDeleted).toHaveBeenCalledWith("att-1", expect.any(Object));
  });

  it("opens the native file picker when the select button is clicked", () => {
    const question = makeQuestion({
      type: "file",
      label: "Upload files",
      file_max_attachments: 1,
    });

    renderWithForm({
      ui: (
        <FileInput
          question={question}
          applicationKey="app-1"
          attachments={[]}
          onAttachmentAdded={vi.fn()}
          onAttachmentDeleted={vi.fn()}
          onAttachmentUpdated={vi.fn()}
        />
      ),
    });

    fireEvent.click(screen.getByRole("button", { name: "Select from computer" }));
    expect(openFileDialogMock).toHaveBeenCalledTimes(1);
  });

  it("shows a validation snackbar when dropzone rejects dropped files", async () => {
    const question = makeQuestion({
      type: "file",
      label: "Upload files",
      file_max_attachments: 1,
    });

    renderWithForm({
      ui: (
        <FileInput
          question={question}
          applicationKey="app-1"
          attachments={[]}
          onAttachmentAdded={vi.fn()}
          onAttachmentDeleted={vi.fn()}
          onAttachmentUpdated={vi.fn()}
        />
      ),
    });

    const onDrop = lastDropzoneOptions.onDrop as ((accepted: File[], rejected: unknown[]) => Promise<void>) | undefined;
    expect(onDrop).toBeDefined();

    await onDrop?.([], [{ errors: [{ message: "Rejected" }] }]);

    expect(showSnackbarMock).toHaveBeenCalledWith(
      "Invalid file type, please ensure it meets the requirements.",
      "error",
    );
  });
});
