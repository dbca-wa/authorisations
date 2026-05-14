import { fireEvent, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { TextInput } from "../../../../components/inputs/text";
import { ERROR_MSG } from "../../../../context/Constants";
import { makeQuestion, renderWithForm } from "./helpers";


describe("TextInput", () => {
  it("renders label and description helper text", () => {
    const question = makeQuestion({ label: "Applicant name", description: "Enter your full name" });

    renderWithForm({ ui: <TextInput question={question} /> });

    expect(screen.getByLabelText("1. Applicant name")).toBeInTheDocument();
    expect(screen.getByText("Enter your full name")).toBeInTheDocument();
  });

  it("trims string values on blur", () => {
    const question = makeQuestion({ label: "Title" });

    renderWithForm({ ui: <TextInput question={question} /> });

    const input = screen.getByLabelText("1. Title") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "  padded value  " } });
    fireEvent.blur(input);

    expect(input.value).toBe("padded value");
  });

  it("shows required error on submit when empty", async () => {
    const question = makeQuestion({ label: "Required field", is_required: true });

    renderWithForm({ ui: <TextInput question={question} /> });

    fireEvent.click(screen.getByRole("button", { name: "Submit" }));

    expect(await screen.findByText(ERROR_MSG.required)).toBeInTheDocument();
  });
});
