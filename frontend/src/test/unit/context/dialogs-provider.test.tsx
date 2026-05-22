import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { DialogProvider } from "../../../context/Dialogs";
import { useDialog } from "../../../context/Hooks";

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
});