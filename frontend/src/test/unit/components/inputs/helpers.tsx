import Button from "@mui/material/Button";
import { render } from "@testing-library/react";
import React from "react";
import { FormProvider, useForm } from "react-hook-form";

import type { IFormAnswers } from "../../../../context/types/Application";
import { Question, type IQuestion } from "../../../../context/types/Questionnaire";

/**
 * Build a questionnaire Question instance with sensible defaults for input tests.
 */
export const makeQuestion = (
  overrides: Partial<IQuestion> = {},
  indices: { step?: number; section?: number; question?: number } = {},
): Question => {
  const base: IQuestion = {
    label: "Question 1",
    type: "text",
    is_required: false,
    description: "Question help text",
  };

  return new Question(
    { ...base, ...overrides },
    {
      step: indices.step ?? 0,
      section: indices.section ?? 0,
      question: indices.question ?? 0,
    },
  );
};

/**
 * Render UI inside react-hook-form context and include a submit trigger.
 */
export const renderWithForm = ({
  ui,
  defaultValues,
  onSubmit,
}: {
  ui: React.ReactNode;
  defaultValues?: IFormAnswers;
  onSubmit?: (values: IFormAnswers) => void;
}) => {
  const Wrapper = ({ children }: { children: React.ReactNode }) => {
    const methods = useForm<IFormAnswers>({
      defaultValues,
      shouldFocusError: false,
    });

    return (
      <FormProvider {...methods}>
        <form onSubmit={methods.handleSubmit((values) => onSubmit?.(values))}>
          {children}
          <Button type="submit">Submit</Button>
        </form>
      </FormProvider>
    );
  };

  return render(<Wrapper>{ui}</Wrapper>);
};
