import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { DialogProvider } from "../../../context/Dialogs";
import { useDialog, useSnackbar } from "../../../context/Hooks";
import { SnackbarProvider } from "../../../context/Snackbar";

const DialogTrigger = ({
  onOpen,
  onClose,
}: {
  onOpen: () => void;
  onClose: () => void;
}) => {
  const { showDialog, hideDialog } = useDialog();

  return (
    <>
      <button
        type="button"
        onClick={() => {
          showDialog({
            title: "Dialog title",
            content: <div>Dialog content</div>,
            actions: (
              <>
                <button type="button">Action</button>
                <button type="button" onClick={hideDialog}>Hide from action</button>
              </>
            ),
            onOpen,
            onClose,
          });
        }}
      >
        Open dialog
      </button>
    </>
  );
};

const SnackbarDialogContent = () => {
  const { showSnackbar } = useSnackbar();

  return (
    <button type="button" onClick={() => showSnackbar("Saved")}>Show snackbar</button>
  );
};

describe("DialogProvider", () => {
  beforeEach(() => {
    vi.spyOn(window, "requestAnimationFrame").mockImplementation((callback: FrameRequestCallback) => {
      callback(0);
      return 1;
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders dialog options and runs onOpen callback", async () => {
    const onOpen = vi.fn();
    const onClose = vi.fn();

    render(
      <DialogProvider>
        <DialogTrigger onOpen={onOpen} onClose={onClose} />
      </DialogProvider>,
    );

    fireEvent.click(screen.getByRole("button", { name: "Open dialog" }));

    expect(await screen.findByText("Dialog title")).toBeInTheDocument();
    expect(screen.getByText("Dialog content")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Action" })).toBeInTheDocument();
    expect(onOpen).toHaveBeenCalledTimes(1);
    expect(onClose).not.toHaveBeenCalled();
  });

  it("closes via top-right close button and runs onClose callback", async () => {
    const onOpen = vi.fn();
    const onClose = vi.fn();

    render(
      <DialogProvider>
        <DialogTrigger onOpen={onOpen} onClose={onClose} />
      </DialogProvider>,
    );

    fireEvent.click(screen.getByRole("button", { name: "Open dialog" }));
    await screen.findByText("Dialog title");

    fireEvent.click(screen.getByRole("button", { name: "close" }));

    await waitFor(() => {
      expect(onClose).toHaveBeenCalledTimes(1);
      expect(screen.queryByText("Dialog title")).not.toBeInTheDocument();
    });
  });

  it("hides dialog through action-scoped hideDialog handler", async () => {
    const onOpen = vi.fn();
    const onClose = vi.fn();

    render(
      <DialogProvider>
        <DialogTrigger onOpen={onOpen} onClose={onClose} />
      </DialogProvider>,
    );

    fireEvent.click(screen.getByRole("button", { name: "Open dialog" }));
    await screen.findByText("Dialog title");

    fireEvent.click(screen.getByRole("button", { name: "Hide from action" }));

    await waitFor(() => {
      expect(onClose).not.toHaveBeenCalled();
      expect(screen.queryByText("Dialog content")).not.toBeInTheDocument();
    });
  });

  it("renders dialog content that can use the snackbar provider", async () => {
    const DialogOpenButton = () => {
      const { showDialog } = useDialog();

      return (
        <button
          type="button"
          onClick={() => {
            showDialog({
              title: "Dialog title",
              content: <SnackbarDialogContent />,
            });
          }}
        >
          Open dialog
        </button>
      );
    };

    render(
      <SnackbarProvider>
        <DialogProvider>
          <DialogOpenButton />
        </DialogProvider>
      </SnackbarProvider>,
    );

    fireEvent.click(screen.getByRole("button", { name: "Open dialog" }));
    fireEvent.click(screen.getByRole("button", { name: "Show snackbar" }));

    expect(await screen.findByText("Saved")).toBeInTheDocument();
  });
});