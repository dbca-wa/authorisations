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
      config: { select_options: ["Research", "Monitoring"] },
    });

    renderWithForm({ ui: <SelectInput question={question} /> });

    fireEvent.mouseDown(screen.getByLabelText("1. Select permit type"));
    expect(screen.getByRole("option", { name: "Research" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "Monitoring" })).toBeInTheDocument();
  });

  it("shows required error in Alert if nothing selected", async () => {
    const question = makeQuestion({
      type: "select",
      label: "Required select",
      is_required: true,
      config: { select_options: ["A", "B"] },
    });

    renderWithForm({ ui: <SelectInput question={question} /> });

    fireEvent.click(screen.getByRole("button", { name: "Submit" }));

    const alert = await screen.findByRole("alert");
    expect(alert).toBeInTheDocument();
    expect(alert).toHaveTextContent(ERROR_MSG.required);
  });
});
