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

  it("submits after verification and confirmation, then switches to read-only mode", async () => {
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
    expect(showSnackbarMock).toHaveBeenCalledWith(
      "Application has been successfully submitted and is read-only now.",
      "success",
    );
    expect(setUserCanEdit).toHaveBeenCalledWith(false);
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

  it("does not initialise Turnstile in read-only mode", () => {
    const setUserCanEdit = vi.fn();

    renderWithForm({
      defaultValues: { 0: { "0-0": "Jane Doe", "0-1": "2026-05-22" } },
      userCanEdit: false,
      setUserCanEdit,
    });

    expect(turnstileRenderMock).not.toHaveBeenCalled();
    expect(screen.queryByText(/Verification failed:/i)).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Submit Application" })).toBeDisabled();
  });
});
