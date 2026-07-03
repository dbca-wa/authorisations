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
        application={makeApplication({ internal_id: "s40-new-1/26-05" })}
        downloadUrl="/d/key-1"
        displayContinue={true}
      />,
    );

    expect(screen.getByText("s40-new-1/26-05")).toBeInTheDocument();
    expect(screen.getByText("Section 40")).toBeInTheDocument();
    expect(screen.getByText("New application (v1)")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Download application PDF" })).toHaveAttribute("href", "/d/key-1");
  });

  it("opens form in new tab when continue is clicked", () => {
    const openNewTabSpy = vi.spyOn(UtilsModule, "openNewTab").mockImplementation(() => undefined);
    const application = makeApplication({ key: "app-key-1" });

    render(
      <ApplicationCard
        process={makeProcess()}
        application={application}
        displayContinue={true}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Continue" }));

    expect(openNewTabSpy).toHaveBeenCalledWith("/a/app-key-1", "app-key-1");
  });

  it("hides continue action when displayContinue is false", () => {
    render(
      <ApplicationCard
        process={makeProcess()}
        application={makeApplication()}
        displayContinue={false}
      />,
    );

    expect(screen.queryByRole("link", { name: "Continue application" })).not.toBeInTheDocument();
  });
});
