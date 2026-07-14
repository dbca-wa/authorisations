import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApplicationCard } from "../../../../../components/layout/main/ApplicationCard";
import * as UtilsModule from "../../../../../context/Utils";
import { makeApplication, makeProcess } from "../../../fixtures";

const { showSnackbarMock } = vi.hoisted(() => ({
  showSnackbarMock: vi.fn(),
}));

vi.mock("../../../../../context/Hooks", async () => {
  const actual = await vi.importActual<typeof import("../../../../../context/Hooks")>("../../../../../context/Hooks");
  return {
    ...actual,
    useSnackbar: () => ({ showSnackbar: showSnackbarMock }),
  };
});


describe("ApplicationCard", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders identifiers and process metadata", () => {
    render(
      <ApplicationCard
        process={makeProcess({ name: "Section 40" })}
        application={makeApplication({ internal_id: "s40-new-1/26-05", status: "SUBMITTED" })}
      />,
    );

    expect(screen.getByText("s40-new-1/26-05")).toBeInTheDocument();
    expect(screen.getByText("Section 40")).toBeInTheDocument();
    expect(screen.getByText("New application (v1)")).toBeInTheDocument();
  });

  it("shows continue button for editable statuses", () => {
    render(
      <ApplicationCard
        process={makeProcess()}
        application={makeApplication({ status: "DRAFT" })}
      />,
    );

    expect(screen.getByRole("button", { name: "Continue" })).toBeInTheDocument();
  });

  it("shows continue button for ACTION_REQUIRED status", () => {
    render(
      <ApplicationCard
        process={makeProcess()}
        application={makeApplication({ status: "ACTION_REQUIRED" })}
      />,
    );

    expect(screen.getByRole("button", { name: "Continue" })).toBeInTheDocument();
  });

  it("hides continue button for non-editable statuses", () => {
    render(
      <ApplicationCard
        process={makeProcess()}
        application={makeApplication({ status: "SUBMITTED" })}
      />,
    );

    expect(screen.queryByRole("button", { name: "Continue" })).not.toBeInTheDocument();
  });

  it("opens form in new tab when continue is clicked", () => {
    const openNewTabSpy = vi.spyOn(UtilsModule, "openNewTab").mockImplementation(() => undefined);
    const application = makeApplication({ key: "app-key-1", status: "DRAFT" });

    render(
      <ApplicationCard
        process={makeProcess()}
        application={application}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Continue" }));

    expect(openNewTabSpy).toHaveBeenCalledWith("/a/app-key-1", "app-key-1");
  });

  it("shows download button for downloadable statuses", () => {
    const application = makeApplication({ status: "SUBMITTED", key: "app-key-123" });
    
    render(
      <ApplicationCard
        process={makeProcess()}
        application={application}
      />,
    );

    const downloadLink = screen.getByRole("link", { name: "Download application PDF" });
    expect(downloadLink).toHaveAttribute("href", `/d/${application.key}`);
  });

  it("hides download button for non-downloadable statuses", () => {
    render(
      <ApplicationCard
        process={makeProcess()}
        application={makeApplication({ status: "DRAFT" })}
      />,
    );

    expect(screen.queryByRole("link", { name: "Download application PDF" })).not.toBeInTheDocument();
  });

  it("does not display review button", () => {
    render(
      <ApplicationCard
        process={makeProcess()}
        application={makeApplication({ status: "SUBMITTED" })}
      />,
    );

    expect(screen.queryByRole("button", { name: "Review" })).not.toBeInTheDocument();
  });
});
