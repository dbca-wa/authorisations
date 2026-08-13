import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import React from "react";
import { FormProvider, useForm } from "react-hook-form";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { FormReviewPage } from "../../../../../components/layout/form/FormReviewPage";
import { makeQuestionnaire } from "../../../fixtures";

import type { IFormAnswers } from "../../../../../context/types/Application";

const {
  submitApplicationMock,
  showSnackbarMock,
  turnstileRenderMock,
  fireConfettiEffectMock,
} = vi.hoisted(() => ({
  submitApplicationMock: vi.fn(),
  showSnackbarMock: vi.fn(),
  turnstileRenderMock: vi.fn(),
  fireConfettiEffectMock: vi.fn(),
}));

vi.mock("../../../../../context/ApiManager", () => ({
  ApiManager: {
    submitApplication: submitApplicationMock,
  },
}));

vi.mock("../../../../../context/Hooks", () => ({
  useSnackbar: () => ({ showSnackbar: showSnackbarMock }),
}));

vi.mock("../../../../../context/TurnstileManager", () => ({
  TurnstileManager: {
    render: turnstileRenderMock,
  },
}));

vi.mock("../../../../../context/confettiEffect", () => ({
  fireConfettiEffect: fireConfettiEffectMock,
}));

vi.mock("../../../../../components/Common", () => ({
  FileAttachmentList: ({ attachments }: { attachments: Array<{ name: string }> }) => (
    <div data-testid="file-list">{attachments.map((attachment) => attachment.name).join(",")}</div>
  ),
}));

const renderWithForm = ({
  defaultValues,
  userCanEdit,
  setUserCanEdit,
}: {
  defaultValues: IFormAnswers;
  userCanEdit: boolean;
  setUserCanEdit: React.Dispatch<React.SetStateAction<boolean>>;
}) => {
  const questionnaire = makeQuestionnaire({
    document: {
      schema_version: "2025.07-1",
      steps: [
        {
          title: "Applicant details",
          description: "",
          sections: [
            {
              title: "Identity",
              description: "",
              questions: [
                {
                  label: "Applicant name",
                  type: "text",
                  is_required: true,
                },
                {
                  label: "Date of birth",
                  type: "date",
                  is_required: false,
                },
              ],
            },
          ],
        },
      ],
    },
  });

  const Wrapper = ({ children }: { children: React.ReactNode }) => {
    const methods = useForm<IFormAnswers>({ defaultValues });
    return <FormProvider {...methods}>{children}</FormProvider>;
  };

  return render(
    <Wrapper>
      <FormReviewPage
        userCanEdit={userCanEdit}
        setUserCanEdit={setUserCanEdit}
        questionnaire={questionnaire.document}
        attachments={[]}
        applicationKey="app-1"
        handleSubmit={(nextStep) => async () => {
          void nextStep;
        }}
      />
    </Wrapper>,
  );
};

describe("FormReviewPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("submits after verification and confirmation, then displays submission modal", async () => {
    const setUserCanEdit = vi.fn();
    submitApplicationMock.mockResolvedValue({ key: "app-1" });
    turnstileRenderMock.mockImplementation(async (_container: unknown, callbacks: { onSuccess?: (token: string) => void }) => {
      callbacks.onSuccess?.("token-123");
      return "widget-1";
    });

    renderWithForm({
      defaultValues: { 0: { "0-0": "Jane Doe", "0-1": "2026-05-22" } },
      userCanEdit: true,
      setUserCanEdit,
    });

    const confirmCheckbox = await screen.findByLabelText(/I confirm that the information provided/i);
    fireEvent.click(confirmCheckbox);

    const submitButton = screen.getByRole("button", { name: "Submit Application" });
    expect(submitButton).toBeEnabled();

    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(submitApplicationMock).toHaveBeenCalledWith("app-1", "token-123");
    });
    
    // Verify modal is displayed after submission
    await waitFor(() => {
      expect(screen.getByText("Application Successfully Submitted")).toBeInTheDocument();
      expect(screen.getByText(/locked in read-only mode/i)).toBeInTheDocument();
    });
    
    expect(setUserCanEdit).toHaveBeenCalledWith(false);
    expect(fireConfettiEffectMock).toHaveBeenCalledWith(5);
  });

  it("shows verification error text when Turnstile reports an error", async () => {
    const setUserCanEdit = vi.fn();
    turnstileRenderMock.mockImplementation(async (_container: unknown, callbacks: { onError?: () => void }) => {
      callbacks.onError?.();
      return "widget-1";
    });

    renderWithForm({
      defaultValues: { 0: { "0-0": "Jane Doe", "0-1": "2026-05-22" } },
      userCanEdit: true,
      setUserCanEdit,
    });

    expect(await screen.findByText(/Verification failed:/i)).toBeInTheDocument();
    expect(submitApplicationMock).not.toHaveBeenCalled();
  });

  it("does not initialise Turnstile in read-only mode and displays modal", () => {
    const setUserCanEdit = vi.fn();

    renderWithForm({
      defaultValues: { 0: { "0-0": "Jane Doe", "0-1": "2026-05-22" } },
      userCanEdit: false,
      setUserCanEdit,
    });

    expect(turnstileRenderMock).not.toHaveBeenCalled();
    expect(screen.queryByText(/Verification failed:/i)).not.toBeInTheDocument();
    
    // Modal should be displayed when userCanEdit is false
    expect(screen.getByText("Application Successfully Submitted")).toBeInTheDocument();
    
    // Submit button should be present but disabled
    const submitButton = screen.getByRole("button", { name: "Submit Application", hidden: true });
    expect(submitButton).toBeDisabled();
  });

  it("shows loading indicator on submit button during submission and disables it", async () => {
    const setUserCanEdit = vi.fn();
    let resolveSubmission!: (value: { key: string }) => void;
    const submissionPromise = new Promise<{ key: string }>((resolve) => {
      resolveSubmission = resolve;
    });
    submitApplicationMock.mockReturnValue(submissionPromise);
    turnstileRenderMock.mockImplementation(async (_container: unknown, callbacks: { onSuccess?: (token: string) => void }) => {
      callbacks.onSuccess?.("token-123");
      return "widget-1";
    });

    renderWithForm({
      defaultValues: { 0: { "0-0": "Jane Doe", "0-1": "2026-05-22" } },
      userCanEdit: true,
      setUserCanEdit,
    });

    const confirmCheckbox = await screen.findByLabelText(/I confirm that the information provided/i);
    fireEvent.click(confirmCheckbox);

    const submitButton = screen.getByRole("button", { name: "Submit Application" });
    expect(submitButton).toBeEnabled();

    fireEvent.click(submitButton);

    // During submission, button should be disabled
    await waitFor(() => {
      expect(submitButton).toBeDisabled();
    });

    // Resolve the submission
    resolveSubmission({ key: "app-1" });

    // After submission completes, modal should appear
    await waitFor(() => {
      expect(screen.getByText("Application Successfully Submitted")).toBeInTheDocument();
    });
  });

  it("re-enables submit button if submission fails", async () => {
    const setUserCanEdit = vi.fn();
    submitApplicationMock.mockRejectedValue(
      new Error("Submission failed")
    );
    turnstileRenderMock.mockImplementation(async (_container: unknown, callbacks: { onSuccess?: (token: string) => void }) => {
      callbacks.onSuccess?.("token-123");
      return "widget-1";
    });

    renderWithForm({
      defaultValues: { 0: { "0-0": "Jane Doe", "0-1": "2026-05-22" } },
      userCanEdit: true,
      setUserCanEdit,
    });

    const confirmCheckbox = await screen.findByLabelText(/I confirm that the information provided/i);
    fireEvent.click(confirmCheckbox);

    const submitButton = screen.getByRole("button", { name: "Submit Application" });
    fireEvent.click(submitButton);

    // Wait for submission to fail and error message to appear
    await waitFor(() => {
      expect(showSnackbarMock).toHaveBeenCalledWith(
        expect.stringContaining("Failed to submit"),
        "error",
      );
    });

    // Button should be re-enabled after failure
    expect(submitButton).toBeEnabled();

    // Modal should NOT appear after failure
    expect(screen.queryByText("Application Successfully Submitted")).not.toBeInTheDocument();
  });



  describe("Turnstile Integration", () => {
    it("disables submit button when Turnstile token is missing", async () => {
      const setUserCanEdit = vi.fn();
      // Mock Turnstile to NOT provide a token
      turnstileRenderMock.mockImplementation(async () => {
        // Simulate no token being generated
        return "widget-1";
      });

      renderWithForm({
        defaultValues: { 0: { "0-0": "Jane Doe", "0-1": "2026-05-22" } },
        userCanEdit: true,
        setUserCanEdit,
      });

      // Confirmation checkbox
      const confirmCheckbox = await screen.findByLabelText(/I confirm that the information provided/i);
      fireEvent.click(confirmCheckbox);

      // Submit button should still be disabled without Turnstile token
      const submitButton = screen.getByRole("button", { name: "Submit Application" });
      expect(submitButton).toBeDisabled();
    });

    it("handles Turnstile widget container initialization error gracefully", async () => {
      const setUserCanEdit = vi.fn();
      // Mock Turnstile render to be called (but container ref might be null in some edge case)
      turnstileRenderMock.mockImplementation(async () => {
        return "widget-1";
      });

      renderWithForm({
        defaultValues: { 0: { "0-0": "Jane Doe", "0-1": "2026-05-22" } },
        userCanEdit: true,
        setUserCanEdit,
      });

      // Verify that Turnstile render was attempted
      await waitFor(() => {
        expect(turnstileRenderMock).toHaveBeenCalled();
      });

      // Submit button should be disabled without successful verification
      const submitButton = screen.getByRole("button", { name: "Submit Application" });
      expect(submitButton).toBeDisabled();
    });
  });
});
