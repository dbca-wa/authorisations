import { fireEvent, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SelectInput } from "../../../../components/inputs/select";
import { ERROR_MSG } from "../../../../context/Constants";
import { makeQuestion, renderWithForm } from "./helpers";


describe("SelectInput", () => {
  it("renders configured options", () => {
    const question = makeQuestion({
      type: "select",
      label: "Select permit type",
      select_options: ["Research", "Monitoring"],
    });

    renderWithForm({ ui: <SelectInput question={question} /> });

    fireEvent.mouseDown(screen.getByLabelText("1. Select permit type"));
    expect(screen.getByRole("option", { name: "Research" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "Monitoring" })).toBeInTheDocument();
  });

  it("shows required error if nothing selected", async () => {
    const question = makeQuestion({
      type: "select",
      label: "Required select",
      is_required: true,
      select_options: ["A", "B"],
    });

    renderWithForm({ ui: <SelectInput question={question} /> });

    fireEvent.click(screen.getByRole("button", { name: "Submit" }));

    expect(await screen.findByText(ERROR_MSG.required)).toBeInTheDocument();
  });
});
