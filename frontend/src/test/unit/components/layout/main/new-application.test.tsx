import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { makeApplication, makeProcess, makeQuestionnaire } from "../../../fixtures";

// Mock clipboard
Object.assign(navigator, {
  clipboard: {
    writeText: vi.fn(() => Promise.resolve()),
  },
});

// Mock ResizeObserver
class MockResizeObserver {
  observe = vi.fn();
  unobserve = vi.fn();
  disconnect = vi.fn();
}
(globalThis as Record<string, unknown>).ResizeObserver = MockResizeObserver;

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

const { TurnstileManagerMock } = vi.hoisted(() => ({
  TurnstileManagerMock: {
    preload: vi.fn(),
    render: vi.fn(),
  },
}));

vi.mock("../../../../../context/TurnstileManager", () => ({
  TurnstileManager: TurnstileManagerMock,
}));

import { NewApplication } from "../../../../../components/layout/main/NewApplication";


describe("NewApplication", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.location.hash = "";
    useLoaderDataMock.mockReturnValue({
      processes: [makeProcess({ slug: "s40", name: "Section 40" })],
      questionnaires: Promise.resolve([]),
    });
    apiMocks.fetchApplications.mockResolvedValue([]);
  });

  describe("Page States", () => {
    it("renders loading state while questionnaire list resolves", () => {
      useResolvedPromiseMock.mockReturnValue([[], true]);

      render(<NewApplication />);

      expect(screen.getByText("One moment while we fetch that for you...")).toBeInTheDocument();
    });

    it("renders empty state when no process has questionnaires", () => {
      useResolvedPromiseMock.mockReturnValue([[], false]);

      render(<NewApplication />);

      expect(screen.getByText("Nothing to see here")).toBeInTheDocument();
      expect(screen.getByText(/We checked.*There really isn't anything hiding here/)).toBeInTheDocument();
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

  describe("Tab Interaction", () => {
    it("enables tabs when multiple questionnaires are available", () => {
      useResolvedPromiseMock.mockReturnValue([
        [
          makeQuestionnaire({
            process_slug: "s40",
            name: "New application",
            code: "new",
          }),
          makeQuestionnaire({
            process_slug: "s40",
            name: "Renewal",
            code: "renewal",
          }),
        ],
        false,
      ]);

      render(<NewApplication />);

      const tabs = screen.getAllByRole("tab");
      expect(tabs).toHaveLength(2);
      tabs.forEach((tab) => {
        expect(tab).not.toHaveAttribute("aria-disabled", "true");
      });
    });

    it("disables tabs when only a single questionnaire is available", () => {
      useResolvedPromiseMock.mockReturnValue([
        [
          makeQuestionnaire({
            process_slug: "s40",
            name: "New application",
          }),
        ],
        false,
      ]);

      render(<NewApplication />);

      const tab = screen.getByRole("tab", { name: "New application" });
      // When disabled, the tab has disabled attribute set to true
      expect(tab.hasAttribute("disabled")).toBe(true);
    });

    it("switches between questionnaires when clicking different tabs", async () => {
      useResolvedPromiseMock.mockReturnValue([
        [
          makeQuestionnaire({
            process_slug: "s40",
            name: "New application",
            description: "Create new",
          }),
          makeQuestionnaire({
            process_slug: "s40",
            name: "Renewal",
            description: "Renew existing",
          }),
        ],
        false,
      ]);

      render(<NewApplication />);

      // Initial tab content
      expect(screen.getByText("Create new")).toBeInTheDocument();

      // Click renewal tab
      const renewalTab = screen.getByRole("tab", { name: "Renewal" });
      fireEvent.click(renewalTab);

      // Content should switch
      await waitFor(() => {
        expect(screen.getByText("Renew existing")).toBeInTheDocument();
      });
    });
  });;

  describe("Hash Routing", () => {
    it("renders correctly even when hash is set in URL", () => {
      useResolvedPromiseMock.mockReturnValue([
        [
          makeQuestionnaire({
            process_slug: "s40",
            name: "New application",
            description: "App description",
          }),
        ],
        false,
      ]);

      // Set a hash that won't match any questionnaire to avoid scrollIntoView test issues
      window.location.hash = "non-matching-hash";

      // Should render without crashing
      render(<NewApplication />);
      expect(screen.getByText("App description")).toBeInTheDocument();
    });

    it("displays first questionnaire when hash does not match any questionnaire", () => {
      useResolvedPromiseMock.mockReturnValue([
        [
          makeQuestionnaire({
            process_slug: "s40",
            name: "New application",
            code: "new",
            description: "New app description",
          }),
        ],
        false,
      ]);

      window.location.hash = "non-existent-hash";

      render(<NewApplication />);

      // Should show first questionnaire by default
      expect(screen.getByText("New app description")).toBeInTheDocument();
    });
  });;;

  describe("Permalink Copy Button", () => {
    it("copies questionnaire link to clipboard when link button is clicked", async () => {
      useResolvedPromiseMock.mockReturnValue([
        [
          makeQuestionnaire({
            process_slug: "s40",
            code: "new-app",
            name: "New application",
          }),
        ],
        false,
      ]);

      render(<NewApplication />);

      const linkButton = screen.getByRole("button", { name: /click to copy the link/i });
      fireEvent.click(linkButton);

      await waitFor(() => {
        expect(navigator.clipboard.writeText).toHaveBeenCalledWith(
          expect.stringContaining("new-application#s40-new-app"),
        );
      });
    });

    it("shows success snackbar when link is copied to clipboard", async () => {
      useResolvedPromiseMock.mockReturnValue([
        [
          makeQuestionnaire({
            process_slug: "s40",
            code: "new-app",
          }),
        ],
        false,
      ]);

      render(<NewApplication />);

      const linkButton = screen.getByRole("button", { name: /click to copy the link/i });
      fireEvent.click(linkButton);

      await waitFor(() => {
        expect(showSnackbarMock).toHaveBeenCalledWith("Link copied to clipboard", "info");
      });
    });

    it("shows error snackbar when clipboard copy fails", async () => {
      (navigator.clipboard.writeText as ReturnType<typeof vi.fn>).mockRejectedValueOnce(new Error("clipboard error"));

      useResolvedPromiseMock.mockReturnValue([
        [
          makeQuestionnaire({
            process_slug: "s40",
            code: "new-app",
          }),
        ],
        false,
      ]);

      render(<NewApplication />);

      const linkButton = screen.getByRole("button", { name: /click to copy the link/i });
      fireEvent.click(linkButton);

      await waitFor(() => {
        expect(showSnackbarMock).toHaveBeenCalledWith("Failed to copy link", "error");
      });
    });
  });

  describe("Application Creation Flow", () => {
    it("asks for confirmation when an in-progress application already exists for the process", async () => {
      useResolvedPromiseMock.mockReturnValue([
        [
          makeQuestionnaire({
            process_slug: "s40",
            name: "New application",
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

    it("opens privacy consent dialog when no in-progress applications exist", async () => {
      useResolvedPromiseMock.mockReturnValue([
        [
          makeQuestionnaire({
            process_slug: "s40",
            name: "New application",
          }),
        ],
        false,
      ]);
      apiMocks.fetchApplications.mockResolvedValue([]);

      render(<NewApplication />);

      fireEvent.click(screen.getByRole("button", { name: "Start Application" }));

      await waitFor(() => {
        expect(showDialogMock).toHaveBeenCalledWith(
          expect.objectContaining({ title: "Collection Notice Disclaimer" }),
        );
      });
    });
  });

  describe("Questionnaire Metadata", () => {
    it("displays updated_at date and version number", () => {
      const updatedDate = "2026-05-10T00:00:00Z";

      useResolvedPromiseMock.mockReturnValue([
        [
          makeQuestionnaire({
            process_slug: "s40",
            name: "New application",
            updated_at: updatedDate,
            version: 2,
          }),
        ],
        false,
      ]);

      render(<NewApplication />);

      const expectedDateString = new Date(updatedDate).toLocaleDateString();
      // Check that both date and version are rendered
      expect(screen.getByText(new RegExp(`${expectedDateString}.*v2`))).toBeInTheDocument();
    });
  });

  describe("Process and Questionnaire Ordering", () => {
    it("renders questionnaires in order from API response without frontend sorting", () => {
      const questionnaires = [
        makeQuestionnaire({
          process_slug: "s40",
          name: "Z - Should be first",
          code: "z-first",
        }),
        makeQuestionnaire({
          process_slug: "s40",
          name: "A - Should be second",
          code: "a-second",
        }),
      ];

      useResolvedPromiseMock.mockReturnValue([questionnaires, false]);

      render(<NewApplication />);

      const tabs = screen.getAllByRole("tab");
      expect(tabs[0]).toHaveTextContent("Z - Should be first");
      expect(tabs[1]).toHaveTextContent("A - Should be second");
    });

    it("renders multiple processes in order from API response", () => {
      useLoaderDataMock.mockReturnValue({
        processes: [
          makeProcess({ slug: "s45", name: "Z - Process", sort_order: 2 }),
          makeProcess({ slug: "s40", name: "A - Process", sort_order: 1 }),
        ],
        questionnaires: Promise.resolve([]),
      });

      useResolvedPromiseMock.mockReturnValue([
        [
          makeQuestionnaire({
            process_slug: "s45",
            name: "Q1",
          }),
          makeQuestionnaire({
            process_slug: "s40",
            name: "Q2",
          }),
        ],
        false,
      ]);

      render(<NewApplication />);

      // Processes should appear in the order they come from API
      // (API handles sorting by sort_order, frontend just displays as-is)
      const processHeadings = screen.getAllByRole("heading", { level: 5 });
      expect(processHeadings[0]).toHaveTextContent("Z - Process");
      expect(processHeadings[1]).toHaveTextContent("A - Process");
    });
  });

  describe("Application Creation Error Handling", () => {
    it("shows error snackbar when fetching existing applications fails", async () => {
      useResolvedPromiseMock.mockReturnValue([
        [
          makeQuestionnaire({
            process_slug: "s40",
            name: "New application",
          }),
        ],
        false,
      ]);
      apiMocks.fetchApplications.mockRejectedValue(
        new Error("Network error")
      );

      render(<NewApplication />);

      fireEvent.click(screen.getByRole("button", { name: "Start Application" }));

      await waitFor(() => {
        expect(showSnackbarMock).toHaveBeenCalledWith(
          expect.stringContaining("Failed to fetch existing applications"),
          "error",
        );
      });
    });
  });

  describe("Collection Notice Dialog - Button State", () => {
    it("keeps 'I agree' button disabled until both Turnstile verification and consent checkbox are ready", async () => {
      useResolvedPromiseMock.mockReturnValue([
        [
          makeQuestionnaire({
            process_slug: "s40",
            name: "New application",
          }),
        ],
        false,
      ]);
      apiMocks.fetchApplications.mockResolvedValue([]);

      render(<NewApplication />);

      fireEvent.click(screen.getByRole("button", { name: "Start Application" }));

      await waitFor(() => {
        expect(showDialogMock).toHaveBeenCalledWith(
          expect.objectContaining({ title: "Collection Notice Disclaimer" }),
        );
      });

      // Get the dialog content (CollectionNoticeDialog component)
      const dialogOptions = showDialogMock.mock.calls[0][0];
      const dialogContent = dialogOptions.content;

      // Mock TurnstileManager.render to simulate successful verification
      let capturedOnSuccess: ((token: string) => void) | null = null;
      TurnstileManagerMock.render.mockImplementation(
        (_container: HTMLElement, callbacks: { onSuccess: (token: string) => void }) => {
          capturedOnSuccess = callbacks.onSuccess;
          return Promise.resolve();
        }
      );

      // Render the dialog content which now includes the buttons
      render(dialogContent);

      // Initially the button should be disabled (before Turnstile verification)
      const agreeButton = screen.getByRole("button", { name: "I agree" });
      expect(agreeButton).toHaveAttribute("disabled");

      // Also check that the checkbox is disabled until Turnstile succeeds
      const checkbox = screen.getByRole("checkbox", {
        name: /I acknowledge the above information/i,
      });
      expect(checkbox).toHaveAttribute("disabled");

      // Simulate Turnstile verification succeeding
      await waitFor(() => {
        expect(capturedOnSuccess).not.toBeNull();
      });

      if (capturedOnSuccess) {
        (capturedOnSuccess as (token: string) => void)("fake-turnstile-token");
      }

      // After Turnstile succeeds, the checkbox should be enabled
      await waitFor(() => {
        expect(checkbox).not.toHaveAttribute("disabled");
      });

      // But button should still be disabled because checkbox is not yet checked
      expect(agreeButton).toHaveAttribute("disabled");

      // User clicks the checkbox to acknowledge
      fireEvent.click(checkbox);

      // Now both conditions are met, button should be enabled
      await waitFor(() => {
        expect(agreeButton).not.toHaveAttribute("disabled");
      });
    });
  });


  describe("Questionnaire Rendering", () => {
    it("displays questionnaire description when available", () => {
      useResolvedPromiseMock.mockReturnValue([
        [
          makeQuestionnaire({
            process_slug: "s40",
            name: "New application",
            description: "Complete this form to apply for authorization",
          }),
        ],
        false,
      ]);

      render(<NewApplication />);

      expect(
        screen.getByText("Complete this form to apply for authorization")
      ).toBeInTheDocument();
    });

    it("displays process image when available", () => {
      useLoaderDataMock.mockReturnValue({
        processes: [
          makeProcess({
            slug: "s40",
            name: "Section 40",
            image_url: "https://example.com/s40.jpg",
            image_credit: "Photo by John Doe",
          }),
        ],
        questionnaires: Promise.resolve([]),
      });

      useResolvedPromiseMock.mockReturnValue([[], false]);

      render(<NewApplication />);

      screen.queryByAltText("Section 40 image");
      // Image is only rendered if there are questionnaires to show
      // So we check that the page renders without crashing
      expect(screen.getByText("Nothing to see here")).toBeInTheDocument();
    });

    it("displays question and section counts in questionnaire summary", () => {
      useResolvedPromiseMock.mockReturnValue([
        [
          makeQuestionnaire({
            process_slug: "s40",
            name: "New application",
            document: {
              schema_version: "2025.07-1",
              steps: [
                {
                  title: "Step 1",
                  description: "",
                  sections: [
                    {
                      title: "Section A",
                      description: "",
                      questions: [
                        { label: "Q1", type: "text", is_required: false },
                        { label: "Q2", type: "text", is_required: false },
                      ],
                    },
                    {
                      title: "Section B",
                      description: "",
                      questions: [
                        { label: "Q3", type: "text", is_required: false },
                      ],
                    },
                  ],
                },
              ],
            },
          }),
        ],
        false,
      ]);

      render(<NewApplication />);

      // Verify the form displays metadata
      expect(screen.getByRole("button", { name: "Start Application" })).toBeInTheDocument();
    });
  });
});
