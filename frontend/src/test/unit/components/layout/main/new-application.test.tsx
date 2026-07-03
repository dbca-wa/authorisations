import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { makeApplication, makeProcess, makeQuestionnaire } from "../../../fixtures";

const {
  apiMocks,
  hideDialogMock,
  navigateMock,
  showDialogMock,
  showSnackbarMock,
  useLoaderDataMock,
  useResolvedPromiseMock,
} = vi.hoisted(() => ({
  apiMocks: {
    fetchApplications: vi.fn(),
  },
  hideDialogMock: vi.fn(),
  navigateMock: vi.fn(),
  showDialogMock: vi.fn(),
  showSnackbarMock: vi.fn(),
  useLoaderDataMock: vi.fn(),
  useResolvedPromiseMock: vi.fn(),
}));

vi.mock("react-router", async () => {
  const actual = await vi.importActual<typeof import("react-router")>("react-router");
  return {
    ...actual,
    useLoaderData: () => useLoaderDataMock(),
    useNavigate: () => navigateMock,
  };
});

vi.mock("../../../../../context/Hooks", async () => {
  const actual = await vi.importActual<typeof import("../../../../../context/Hooks")>("../../../../../context/Hooks");
  return {
    ...actual,
    useResolvedPromise: (...args: unknown[]) => useResolvedPromiseMock(...args),
    useDialog: () => ({ showDialog: showDialogMock, hideDialog: hideDialogMock }),
    useSnackbar: () => ({ showSnackbar: showSnackbarMock }),
  };
});

vi.mock("../../../../../context/ApiManager", () => ({
  ApiManager: apiMocks,
}));

vi.mock("../../../../../context/TurnstileManager", () => ({
  TurnstileManager: {
    preload: vi.fn(),
  },
}));

import { NewApplication } from "../../../../../components/layout/main/NewApplication";


describe("NewApplication", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useLoaderDataMock.mockReturnValue({
      processes: [makeProcess({ slug: "s40", name: "Section 40" })],
      questionnaires: Promise.resolve([]),
    });
    apiMocks.fetchApplications.mockResolvedValue([]);
  });

  it("renders loading state while questionnaire list resolves", () => {
    useResolvedPromiseMock.mockReturnValue([[], true]);

    render(<NewApplication />);

    expect(screen.getByText("Loading questionnaires...")).toBeInTheDocument();
  });

  it("renders empty state when no process has questionnaires", () => {
    useResolvedPromiseMock.mockReturnValue([[], false]);

    render(<NewApplication />);

    expect(screen.getByText("No items found")).toBeInTheDocument();
  });

  it("renders process group and questionnaire details when data exists", () => {
    useResolvedPromiseMock.mockReturnValue([
      [
        makeQuestionnaire({
          process_slug: "s40",
          name: "New application",
          description: "Create a new application",
        }),
      ],
      false,
    ]);

    render(<NewApplication />);

    expect(screen.getByText("Section 40")).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "New application" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Start Application" })).toBeInTheDocument();
  });

  it("asks for confirmation when an in-progress application already exists for the process", async () => {
    useResolvedPromiseMock.mockReturnValue([
      [
        makeQuestionnaire({
          process_slug: "s40",
          name: "New application",
          description: "Create a new application",
        }),
      ],
      false,
    ]);
    apiMocks.fetchApplications.mockResolvedValue([
      makeApplication({ process_slug: "s40", status: "DRAFT" }),
    ]);

    render(<NewApplication />);

    fireEvent.click(screen.getByRole("button", { name: "Start Application" }));

    await waitFor(() => {
      expect(apiMocks.fetchApplications).toHaveBeenCalledTimes(1);
      expect(showDialogMock).toHaveBeenCalledWith(
        expect.objectContaining({ title: "Create a new application?" }),
      );
    });
  });

  it("opens privacy consent dialog directly when only finalised applications exist", async () => {
    useResolvedPromiseMock.mockReturnValue([
      [
        makeQuestionnaire({
          process_slug: "s40",
          name: "New application",
          description: "Create a new application",
        }),
      ],
      false,
    ]);
    apiMocks.fetchApplications.mockResolvedValue([
      makeApplication({ process_slug: "s40", status: "APPROVED" }),
    ]);

    render(<NewApplication />);

    fireEvent.click(screen.getByRole("button", { name: "Start Application" }));

    await waitFor(() => {
      expect(showDialogMock).toHaveBeenCalledWith(
        expect.objectContaining({ title: "Collection Notice Disclaimer" }),
      );
    });
  });

  it("shows a snackbar error when fetching existing applications fails", async () => {
    useResolvedPromiseMock.mockReturnValue([
      [
        makeQuestionnaire({
          process_slug: "s40",
          name: "New application",
        }),
      ],
      false,
    ]);
    apiMocks.fetchApplications.mockRejectedValue(new Error("network down"));

    render(<NewApplication />);

    fireEvent.click(screen.getByRole("button", { name: "Start Application" }));

    await waitFor(() => {
      expect(showSnackbarMock).toHaveBeenCalledWith(
        "Failed to fetch existing applications, please try again later. If problem persists, contact support.",
        "error",
      );
      expect(showDialogMock).not.toHaveBeenCalled();
    });
  });

  it("displays the updated_at date in the Last updated field, not created_at", () => {
    const createdDate = "2026-05-01T00:00:00Z";
    const updatedDate = "2026-05-10T00:00:00Z";

    useResolvedPromiseMock.mockReturnValue([
      [
        makeQuestionnaire({
          process_slug: "s40",
          name: "New application",
          created_at: createdDate,
          updated_at: updatedDate,
        }),
      ],
      false,
    ]);

    render(<NewApplication />);

    // The updated_at date should be formatted as 5/10/2026 (US locale from new Date)
    const expectedDateString = new Date(updatedDate).toLocaleDateString();
    expect(screen.getByText(`Last updated: ${expectedDateString} (v1)`)).toBeInTheDocument();
  });
});
