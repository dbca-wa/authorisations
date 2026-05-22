import { fireEvent, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { CheckboxInput } from "../../../../components/inputs/checkbox";
import { ERROR_MSG } from "../../../../context/Constants";
import { makeQuestion, renderWithForm } from "./helpers";


describe("CheckboxInput", () => {
  it("renders label and description", () => {
    const question = makeQuestion({ type: "checkbox", label: "Accept terms", description: "You must accept" });

    renderWithForm({ ui: <CheckboxInput question={question} /> });

    expect(screen.getByLabelText("1. Accept terms")).toBeInTheDocument();
    expect(screen.getByText("You must accept")).toBeInTheDocument();
  });

  it("toggles checkbox state when clicked", () => {
    const question = makeQuestion({ type: "checkbox", label: "Confirm" });

    renderWithForm({ ui: <CheckboxInput question={question} /> });

    const checkbox = screen.getByLabelText("1. Confirm") as HTMLInputElement;
    expect(checkbox.checked).toBe(false);

    fireEvent.click(checkbox);
    expect(checkbox.checked).toBe(true);
  });

  it("shows required error when required checkbox is not checked", async () => {
    const question = makeQuestion({ type: "checkbox", label: "Required confirm", is_required: true });

    renderWithForm({ ui: <CheckboxInput question={question} /> });

    fireEvent.click(screen.getByRole("button", { name: "Submit" }));

    expect(await screen.findByText(ERROR_MSG.required)).toBeInTheDocument();
  });
});
