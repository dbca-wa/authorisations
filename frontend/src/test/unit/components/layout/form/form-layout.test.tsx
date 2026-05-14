import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ERROR_MSG } from "../../../../../context/Constants";
import { FormLayout } from "../../../../../components/layout/form/FormLayout";
import { makeApplication, makeQuestionnaire } from "../../../fixtures";


const useLoaderDataMock = vi.fn();
const showSnackbarMock = vi.fn();

const { apiMocks } = vi.hoisted(() => ({
  apiMocks: {
    updateApplication: vi.fn(),
  },
}));

const turnstileRenderMock = vi.fn();

vi.mock("react-router", async () => {
  const actual = await vi.importActual<typeof import("react-router")>("react-router");
  return {
    ...actual,
    useLoaderData: () => useLoaderDataMock(),
  };
});

vi.mock("../../../../../context/Hooks", async () => {
  const actual = await vi.importActual<typeof import("../../../../../context/Hooks")>("../../../../../context/Hooks");
  return {
    ...actual,
    useSnackbar: () => ({ showSnackbar: showSnackbarMock }),
  };
});

vi.mock("../../../../../context/ApiManager", () => ({
  ApiManager: apiMocks,
}));

vi.mock("../../../../../context/TurnstileManager", () => ({
  TurnstileManager: {
    render: turnstileRenderMock,
  },
}));

vi.mock("../../../../../context/Utils", async () => {
  const actual = await vi.importActual<typeof import("../../../../../context/Utils")>("../../../../../context/Utils");
  return {
    ...actual,
    scrollToTop: vi.fn(),
  };
});


describe("FormLayout", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    Object.defineProperty(window.navigator, "onLine", {
      configurable: true,
      value: true,
    });

    window.HTMLElement.prototype.scrollIntoView = vi.fn();

    const questionnaire = makeQuestionnaire({
      document: {
        schema_version: "2025.07-1",
        steps: [
          {
            title: "Applicant details",
            description: "Provide the applicant name",
            sections: [
              {
                title: "Identity",
                description: "",
                questions: [
                  {
                    label: "Applicant name",
                    type: "text",
                    is_required: true,
                    description: "Enter the applicant's full name",
                  },
                ],
              },
            ],
          },
        ],
      },
    });

    const application = makeApplication({
      status: "DRAFT",
      document: {
        schema_version: "2025.07-1",
        active_step: 0,
        steps: [
          {
            is_valid: null,
            answers: {},
          },
        ],
      },
    });

    useLoaderDataMock.mockReturnValue({
      app: application,
      questionnaire,
      attachments: [],
    });

    apiMocks.updateApplication.mockResolvedValue(application);
    turnstileRenderMock.mockImplementation(async (_container: unknown, callbacks: { onSuccess?: (token: string) => void }) => {
      callbacks.onSuccess?.("turnstile-token");
      return "turnstile-widget";
    });
  });

  it("keeps the user on the current step and shows validation when a required field is empty", async () => {
    render(<FormLayout />);

    fireEvent.click(screen.getByRole("button", { name: "Continue" }));

    expect(await screen.findByText(ERROR_MSG.required)).toBeInTheDocument();
    expect(apiMocks.updateApplication).not.toHaveBeenCalled();
    expect(screen.getByLabelText(/Applicant name/)).toBeInTheDocument();
  });

  it("submits a valid step, moves to review, and allows returning via the sidebar", async () => {
    render(<FormLayout />);

    fireEvent.change(screen.getByLabelText(/Applicant name/), {
      target: { value: "Jane Doe" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Continue" }));

    await screen.findByText("Review your answers");
    expect(apiMocks.updateApplication).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByRole("button", { name: "Applicant details" }));

    await waitFor(() => {
      expect(screen.getByLabelText(/Applicant name/)).toBeInTheDocument();
    });
  });
});