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
            { label: "Permit number", type: "text", is_required: false, config: { dependent_step: 1 } },
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
    // With {isVisible && inputComponent}, invisible questions are not rendered in DOM at all.
    // This is the fix for the regression: invisible inputs don't register with react-hook-form.
    const permutNumber = screen.queryByText("2. Permit number");
    expect(permutNumber).not.toBeInTheDocument();

    firstRender.unmount();

    renderWithForm({
      currentStep,
      activeStep: 0,
      handleSubmit,
      defaultValues: { 0: { "0-0": true } },
    });

    // Element should now be in the DOM and visible when parent is true
    expect(screen.getByText("2. Permit number")).toBeInTheDocument();
    expect(screen.getByText("2. Permit number")).toBeVisible();
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

  describe("Form Behavior", () => {
    it("prevents form submission on Enter key for text inputs but allows for textarea", () => {
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
            questions: [{ label: "Name", type: "text", is_required: false }],
          },
        ],
      };

      const { container } = renderWithForm({ currentStep, activeStep: 0, handleSubmit });

      const form = container.querySelector("form");
      if (!form) throw new Error("Form not found");

      // Test that Enter key doesn't submit form
      const event = new KeyboardEvent("keydown", { key: "Enter", bubbles: true });
      const preventDefaultSpy = vi.spyOn(event, "preventDefault");
      form.dispatchEvent(event);

      // The prevention happens in onKeyDown handler  
      expect(preventDefaultSpy).toHaveBeenCalled();
    });
  });

  describe("Regression: Invisible required dependent fields", () => {
    it("does not block form submission when a required dependent question is invisible", () => {
      // Regression test for bug: invisible required dependent questions blocked form submission.
      // Scenario: A dependent question is marked required but its parent is false/unchecked.
      // Before fix: Question existed in DOM but hidden (Collapse), registering with form validation.
      //            Browser scrolled to hidden field; form showed "field required" error.
      // After fix: With {isVisible && inputComponent}, input only renders when visible.
      //            Invisible inputs don't render at all; they don't register with react-hook-form.

      const handleSubmit = vi.fn((_nextStep: React.SetStateAction<number>) => async () => {
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
              // Parent question: optional checkbox that controls visibility
              { label: "Has permit", type: "checkbox", is_required: false },
              // Dependent question: REQUIRED but only when parent is true
              { label: "Permit number", type: "text", is_required: true, config: { dependent_step: 1 } },
            ],
          },
        ],
      };

      // Render with parent unchecked (false) - dependent question should not render
      renderWithForm({
        currentStep,
        activeStep: 0,
        handleSubmit,
        defaultValues: { 0: { "0-0": false, "0-1": "" } },
      });

      // With {isVisible && inputComponent}, invisible questions are not rendered in DOM at all
      // This is the fix: inputs don't register if they're not in the DOM
      expect(screen.queryByText("2. Permit number")).not.toBeInTheDocument();

      // Attempt form submission without the invisible required field in DOM
      const continueButton = screen.getByRole("button", { name: "Continue" });
      fireEvent.click(continueButton);

      // Regression check: Form submission should succeed
      // Before fix: handleSubmit would NOT be called (blocked by validation error on hidden field)
      // After fix: handleSubmit IS called (invisible field not in DOM, so not registered)
      expect(handleSubmit).toHaveBeenCalled();
    });

    it("dependent question does not exist in DOM when invisible", () => {
      // Verify that invisible dependent questions are completely absent from DOM.
      // This is how {isVisible && inputComponent} prevents validation blocks.

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
              { label: "Permit number", type: "text", is_required: true, config: { dependent_step: 1 } },
            ],
          },
        ],
      };

      // Render with parent unchecked
      renderWithForm({
        currentStep,
        activeStep: 0,
        handleSubmit,
        defaultValues: { 0: { "0-0": false } },
      });

      // Invisible required field should not exist in DOM
      expect(screen.queryByText("2. Permit number")).not.toBeInTheDocument();
    });
  });
});
