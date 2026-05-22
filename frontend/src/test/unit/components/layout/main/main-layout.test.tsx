import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { makeProcess } from "../../../fixtures";

const useLoaderDataMock = vi.fn();
const navigateMock = vi.fn();

vi.mock("react-router", async () => {
  const actual = await vi.importActual<typeof import("react-router")>("react-router");
  return {
    ...actual,
    useLoaderData: () => useLoaderDataMock(),
    useNavigate: () => navigateMock,
  };
});

vi.mock("../../../../../router", () => ({
  ROUTES: [
    {
      label: "My applications",
      path: "/my-applications",
      icon: <span>Icon</span>,
      divider: false,
    },
    {
      label: "Privacy Policy",
      path: "/privacy",
      icon: <span>Privacy</span>,
      divider: false,
      sidebar: false,
    },
  ],
}));

import { MainLayout } from "../../../../../components/layout/main/MainLayout";


describe("MainLayout", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useLoaderDataMock.mockReturnValue({
      processes: [makeProcess()],
    });
    window.history.pushState({}, "", "/my-applications");
  });

  it("updates document title based on active route", () => {
    render(
      <MainLayout
        route={{
          label: "My applications",
          path: "/my-applications",
          icon: <span>Icon</span>,
          divider: false,
          component: () => <div>Page Content</div>,
        }}
      />,
    );

    expect(document.title).toBe("My applications : DBCA Authorisations");
    expect(screen.getByText("Page Content")).toBeInTheDocument();
  });

  it("navigates when footer route is clicked", () => {
    render(
      <MainLayout
        route={{
          label: "My applications",
          path: "/my-applications",
          icon: <span>Icon</span>,
          divider: false,
          component: () => <div>Page Content</div>,
        }}
      />,
    );

    fireEvent.click(screen.getByLabelText("Privacy Policy"));

    expect(navigateMock).toHaveBeenCalledWith("/privacy", { viewTransition: true });
  });
});
