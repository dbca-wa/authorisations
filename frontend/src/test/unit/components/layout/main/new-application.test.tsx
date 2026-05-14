import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { makeProcess, makeQuestionnaire } from "../../../fixtures";

const useLoaderDataMock = vi.fn();
const useResolvedPromiseMock = vi.fn();

vi.mock("react-router", async () => {
  const actual = await vi.importActual<typeof import("react-router")>("react-router");
  return {
    ...actual,
    useLoaderData: () => useLoaderDataMock(),
    useNavigate: () => vi.fn(),
  };
});

vi.mock("../../../../../context/Hooks", async () => {
  const actual = await vi.importActual<typeof import("../../../../../context/Hooks")>("../../../../../context/Hooks");
  return {
    ...actual,
    useResolvedPromise: (...args: unknown[]) => useResolvedPromiseMock(...args),
    useDialog: () => ({ showDialog: vi.fn(), hideDialog: vi.fn() }),
    useSnackbar: () => ({ showSnackbar: vi.fn() }),
  };
});

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
});
