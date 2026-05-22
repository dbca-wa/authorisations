import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { AlertColor } from "@mui/material/Alert";
import type { ReactNode } from "react";

import { useSnackbar } from "../../../context/Hooks";
import { SnackbarProvider } from "../../../context/Snackbar";

vi.mock("@mui/material/Snackbar", () => {
  return {
    default: ({
      children,
      open,
      autoHideDuration,
      onClose,
      slotProps,
    }: {
      children: ReactNode;
      open: boolean;
      autoHideDuration: number;
      onClose?: (event: unknown, reason?: "timeout" | "clickaway") => void;
      slotProps?: { transition?: { onExited?: () => void } };
    }) => (
      <div data-testid="mui-snackbar" data-open={String(open)} data-auto-hide-duration={String(autoHideDuration)}>
        {children}
        <button type="button" onClick={() => onClose?.({}, "clickaway")}>clickaway</button>
        <button
          type="button"
          onClick={() => {
            onClose?.({}, "timeout");
            slotProps?.transition?.onExited?.();
          }}
        >
          timeout
        </button>
      </div>
    ),
  };
});

vi.mock("@mui/material/Alert", () => {
  return {
    default: ({
      children,
      severity,
      onClose,
    }: {
      children: ReactNode;
      severity: AlertColor;
      onClose?: () => void;
    }) => (
      <div data-testid="mui-alert" data-severity={severity}>
        <span>{children}</span>
        <button type="button" onClick={onClose}>close-alert</button>
      </div>
    ),
  };
});

const SnackbarTrigger = () => {
  const { showSnackbar } = useSnackbar();

  return (
    <>
      <button type="button" onClick={() => showSnackbar("All good", "success")}>Show success</button>
      <button type="button" onClick={() => showSnackbar("Something broke", "error")}>Show error</button>
    </>
  );
};

describe("SnackbarProvider", () => {
  it("shows success and error notifications with respective durations", () => {
    render(
      <SnackbarProvider>
        <SnackbarTrigger />
      </SnackbarProvider>,
    );

    fireEvent.click(screen.getByRole("button", { name: "Show success" }));
    fireEvent.click(screen.getByRole("button", { name: "Show error" }));

    const snackbars = screen.getAllByTestId("mui-snackbar");
    expect(screen.getByText("All good")).toBeInTheDocument();
    expect(screen.getByText("Something broke")).toBeInTheDocument();
    expect(snackbars[0]).toHaveAttribute("data-auto-hide-duration", "4000");
    expect(snackbars[1]).toHaveAttribute("data-auto-hide-duration", "8000");
  });

  it("ignores clickaway and dismisses notification on timeout", () => {
    render(
      <SnackbarProvider>
        <SnackbarTrigger />
      </SnackbarProvider>,
    );

    fireEvent.click(screen.getByRole("button", { name: "Show success" }));

    fireEvent.click(screen.getByRole("button", { name: "clickaway" }));
    expect(screen.getByText("All good")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "timeout" }));
    expect(screen.queryByText("All good")).not.toBeInTheDocument();
  });
});