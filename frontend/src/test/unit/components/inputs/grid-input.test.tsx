import { fireEvent, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { GridInput } from "../../../../components/inputs/grid";
import { makeQuestion, renderWithForm } from "./helpers";


describe("GridInput", () => {
  it("renders heading, description and add-record control", () => {
    const question = makeQuestion({
      type: "grid",
      label: "Animal details",
      description: "Provide one row per animal",
      grid_columns: [
        { label: "Species", type: "text", description: "Species common name" },
        { label: "Count", type: "number" },
      ],
    });

    renderWithForm({ ui: <GridInput question={question} /> });

    expect(screen.getByText("1. Animal details")).toBeInTheDocument();
    expect(screen.getByText("Provide one row per animal")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Add Record" })).toBeInTheDocument();
  });

  it("shows required validation when no rows are provided", async () => {
    const question = makeQuestion({
      type: "grid",
      label: "Required grid",
      is_required: true,
      grid_columns: [{ label: "Species", type: "text" }],
    });

    renderWithForm({ ui: <GridInput question={question} /> });

    fireEvent.click(screen.getByRole("button", { name: "Submit" }));

    expect(await screen.findByText("At least one record must be provided.")).toBeInTheDocument();
  });

  it("does not show required validation when at least one row already exists", async () => {
    const question = makeQuestion({
      type: "grid",
      label: "Required grid",
      is_required: true,
      grid_columns: [{ label: "Species", type: "text" }],
    });

    renderWithForm({
      ui: <GridInput question={question} />,
      defaultValues: {
        0: {
          "0-0": [{ Species: "Quokka" }],
        },
      },
    });

    fireEvent.click(screen.getByRole("button", { name: "Submit" }));

    expect(screen.queryByText("At least one record must be provided.")).not.toBeInTheDocument();
  });
});
