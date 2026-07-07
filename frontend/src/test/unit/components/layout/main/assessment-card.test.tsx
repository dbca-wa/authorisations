import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AssessmentCard } from "../../../../../components/layout/main/AssessmentCard";
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


describe("AssessmentCard", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
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

  it("always displays the review button", () => {
    render(
      <AssessmentCard
        process={makeProcess()}
        application={makeApplication()}
      />,
    );

    expect(screen.getByRole("button", { name: "Review" })).toBeInTheDocument();
  });

  it("opens application in new tab when review is clicked", () => {
    const openNewTabSpy = vi.spyOn(UtilsModule, "openNewTab").mockImplementation(() => undefined);
    const application = makeApplication({ key: "app-key-1" });

    render(
      <AssessmentCard
        process={makeProcess()}
        application={application}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Review" }));

    expect(openNewTabSpy).toHaveBeenCalledWith("/a/app-key-1", "app-key-1");
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
