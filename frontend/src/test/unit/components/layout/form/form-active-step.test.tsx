import { fireEvent, render, screen } from "@testing-library/react";
import React from "react";
import { FormProvider, useForm } from "react-hook-form";
import { describe, expect, it, vi } from "vitest";

import { FormActiveStep } from "../../../../../components/layout/form/FormActiveStep";

import type { IApplicationAttachment, IFormAnswers } from "../../../../../context/types/Application";
import type { AsyncVoidAction } from "../../../../../context/types/Generic";
import type { IFormStep } from "../../../../../context/types/Questionnaire";

vi.mock("../../../../../components/inputs/text", () => ({
  TextInput: ({ question }: { question: { labelText: string } }) => <div>{question.labelText}</div>,
}));

vi.mock("../../../../../components/inputs/checkbox", () => ({
  CheckboxInput: ({ question }: { question: { labelText: string } }) => <div>{question.labelText}</div>,
}));

vi.mock("../../../../../components/inputs/select", () => ({
  SelectInput: ({ question }: { question: { labelText: string } }) => <div>{question.labelText}</div>,
}));

vi.mock("../../../../../components/inputs/date", () => ({
  DateInput: ({ question }: { question: { labelText: string } }) => <div>{question.labelText}</div>,
}));

vi.mock("../../../../../components/inputs/grid", () => ({
  GridInput: ({ question }: { question: { labelText: string } }) => <div>{question.labelText}</div>,
}));

vi.mock("../../../../../components/inputs/file", () => ({
  FileInput: ({ question }: { question: { labelText: string } }) => <div>{question.labelText}</div>,
}));

const renderWithForm = ({
  currentStep,
  activeStep,
  defaultValues,
  handleSubmit,
  attachments = [],
}: {
  currentStep: IFormStep;
  activeStep: number;
  defaultValues?: IFormAnswers;
  handleSubmit: (nextStep: React.SetStateAction<number>) => AsyncVoidAction;
  attachments?: IApplicationAttachment[];
}) => {
  const Wrapper = ({ children }: { children: React.ReactNode }) => {
    const methods = useForm<IFormAnswers>({ defaultValues });
    return <FormProvider {...methods}>{children}</FormProvider>;
  };

  return render(
    <Wrapper>
      <FormActiveStep
        handleSubmit={handleSubmit}
        onAttachmentAdded={vi.fn()}
        onAttachmentDeleted={vi.fn()}
        onAttachmentUpdated={vi.fn()}
        applicationKey="app-1"
        currentStep={currentStep}
        attachments={attachments}
        activeStep={activeStep}
      />
    </Wrapper>,
  );
};

describe("FormActiveStep", () => {
  it("hides the back button on first step and shows continue", () => {
    const handleSubmit = vi.fn((nextStep: React.SetStateAction<number>) => async () => {
      void nextStep;
    });

    const currentStep: IFormStep = {
      title: "Step 1",
      description: "",
      sections: [
        {
          title: "Section 1",
          description: "",
          questions: [{ label: "Applicant name", type: "text", is_required: false }],
        },
      ],
    };

    renderWithForm({ currentStep, activeStep: 0, handleSubmit });

    expect(screen.queryByRole("button", { name: "Back" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Continue" })).toBeInTheDocument();
  });

  it("shows dependent questions only when parent answer is truthy", () => {
    const handleSubmit = vi.fn(() => async () => {
      return;
    });

    const currentStep: IFormStep = {
      title: "Step 1",
      description: "",
      sections: [
        {
          title: "Section 1",
          description: "",
          questions: [
            { label: "Has permit", type: "checkbox", is_required: false },
            { label: "Permit number", type: "text", is_required: false, dependent_step: 1 },
          ],
        },
      ],
    };

    const firstRender = renderWithForm({
      currentStep,
      activeStep: 0,
      handleSubmit,
      defaultValues: { 0: { "0-0": false } },
    });

    expect(screen.getByText("1. Has permit")).toBeInTheDocument();
    expect(screen.queryByText("2. Permit number")).not.toBeInTheDocument();

    firstRender.unmount();

    renderWithForm({
      currentStep,
      activeStep: 0,
      handleSubmit,
      defaultValues: { 0: { "0-0": true } },
    });

    expect(screen.getByText("2. Permit number")).toBeInTheDocument();
  });

  it("throws for unsupported question types", () => {
    const handleSubmit = vi.fn(() => async () => {
      return;
    });

    const currentStep: IFormStep = {
      title: "Step 1",
      description: "",
      sections: [
        {
          title: "Section 1",
          description: "",
          questions: [{ label: "Unknown", type: "mystery", is_required: false }],
        },
      ],
    };

    expect(() => {
      renderWithForm({ currentStep, activeStep: 0, handleSubmit });
    }).toThrow("Unknown question type: mystery");
  });

  it("renders back button and triggers previous-step handler on non-first step", () => {
    const handleSubmit = vi.fn((nextStep: React.SetStateAction<number>) => async () => {
      void nextStep;
    });

    const currentStep: IFormStep = {
      title: "Step 2",
      description: "",
      sections: [
        {
          title: "Section 1",
          description: "",
          questions: [{ label: "Summary", type: "text", is_required: false }],
        },
      ],
    };

    renderWithForm({ currentStep, activeStep: 1, handleSubmit });

    fireEvent.click(screen.getByRole("button", { name: "Back" }));
    expect(handleSubmit).toHaveBeenCalled();
  });
});
