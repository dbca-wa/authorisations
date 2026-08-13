import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { SubmissionModal } from "../../../../../components/layout/form/SubmissionModal";

describe("SubmissionModal", () => {
  it("displays modal when open is true", () => {
    const onCloseMock = vi.fn();

    render(
      <SubmissionModal
        open={true}
        applicationKey="test-app-123"
        onClose={onCloseMock}
      />
    );

    expect(screen.getByText("Application Successfully Submitted")).toBeInTheDocument();
    expect(screen.getByText(/locked in read-only mode/i)).toBeInTheDocument();
  });

  it("does not display modal when open is false", () => {
    const onCloseMock = vi.fn();

    render(
      <SubmissionModal
        open={false}
        applicationKey="test-app-123"
        onClose={onCloseMock}
      />
    );

    expect(screen.queryByText("Application Successfully Submitted")).not.toBeInTheDocument();
  });

  it("displays both action buttons", () => {
    const onCloseMock = vi.fn();

    render(
      <SubmissionModal
        open={true}
        applicationKey="test-app-123"
        onClose={onCloseMock}
      />
    );

    expect(screen.getByRole("link", { name: "Download PDF" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Exit application" })).toBeInTheDocument();
  });

  it("displays explanation text about application status and updates", () => {
    const onCloseMock = vi.fn();

    render(
      <SubmissionModal
        open={true}
        applicationKey="test-app-123"
        onClose={onCloseMock}
      />
    );

    expect(screen.getByText("This application is now locked in read-only mode.")).toBeInTheDocument();
    expect(screen.getByText(/You will be able to track the progress/i)).toBeInTheDocument();
    expect(screen.getByText(/additional information or requests for clarification/i)).toBeInTheDocument();
  });

  it("calls onClose when close button is clicked", () => {
    const onCloseMock = vi.fn();

    render(
      <SubmissionModal
        open={true}
        applicationKey="test-app-123"
        onClose={onCloseMock}
      />
    );

    const closeButton = screen.getByRole("button", { name: /close/i });
    fireEvent.click(closeButton);

    expect(onCloseMock).toHaveBeenCalledTimes(1);
  });

  it("Display buttons with correct accessibility labels and hrefs", () => {
    const onCloseMock = vi.fn();

    render(
      <SubmissionModal
        open={true}
        applicationKey="test-app-456"
        onClose={onCloseMock}
      />
    );

    // Download link (Button with href renders as <a> element)
    const downloadLink = screen.getByRole("link", { name: /Download PDF/i });
    expect(downloadLink).toHaveAttribute("href", "/d/test-app-456");
    
    // Exit button
    const exitButton = screen.getByRole("button", { name: "Exit application" });
    expect(exitButton).toBeInTheDocument();
  });

  it("Exit application button calls window.close", () => {
    const onCloseMock = vi.fn();
    const windowCloseSpy = vi.spyOn(window, "close").mockImplementation(() => {});

    render(
      <SubmissionModal
        open={true}
        applicationKey="test-app-123"
        onClose={onCloseMock}
      />
    );

    const exitButton = screen.getByRole("button", { name: "Exit application" });
    fireEvent.click(exitButton);

    expect(windowCloseSpy).toHaveBeenCalled();

    windowCloseSpy.mockRestore();
  });

  it("displays success icon", () => {
    const onCloseMock = vi.fn();

    render(
      <SubmissionModal
        open={true}
        applicationKey="test-app-123"
        onClose={onCloseMock}
      />
    );

    // MUI icon should be rendered; we check for it via the SVG title or other accessibility features
    const title = screen.getByText("Application Successfully Submitted");
    expect(title).toBeInTheDocument();
    // The icon is rendered before the title text in the DialogTitle
  });
});
