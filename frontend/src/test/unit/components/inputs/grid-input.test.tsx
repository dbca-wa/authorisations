import { fireEvent, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { GridInput } from "../../../../components/inputs/grid";
import { makeQuestion, renderWithForm } from "./helpers";

const buildGridQuestion = (overrides: Record<string, unknown> = {}) =>
  makeQuestion({
    type: "grid",
    label: "Animal details",
    description: "Provide one row per animal",
    config: {
      grid_columns: [
        { label: "Species", type: "text" },
        { label: "Notes", type: "textarea" },
        { label: "Count", type: "number" },
        { label: "Approved", type: "checkbox" },
        { label: "Category", type: "select", select_options: ["Mammal", "Bird"] },
        { label: "First seen", type: "date" },
      ],
    },
    ...overrides,
  });


describe("GridInput", () => {
  it("renders heading, description and add-record control", () => {
    const question = makeQuestion({
      type: "grid",
      label: "Animal details",
      description: "Provide one row per animal",
      config: {
        grid_columns: [
          { label: "Species", type: "text", description: "Species common name" },
          { label: "Count", type: "number" },
        ],
      },
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
      config: { grid_columns: [{ label: "Species", type: "text" }] },
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
      config: { grid_columns: [{ label: "Species", type: "text" }] },
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

  it("creates a full default row payload for every supported grid column type", async () => {
    const user = userEvent.setup();
    const question = buildGridQuestion();
    const onSubmit = vi.fn();
    renderWithForm({ ui: <GridInput question={question} />, onSubmit });

    fireEvent.click(screen.getByRole("button", { name: "Add Record" }));
    await user.click(screen.getByRole("button", { name: "Save" }));
    await user.click(screen.getByRole("button", { name: "Submit" }));

    expect(screen.getByText("Species")).toBeInTheDocument();
    expect(screen.getByText("Notes")).toBeInTheDocument();
    expect(screen.getByText("Count")).toBeInTheDocument();
    expect(screen.getByText("Approved")).toBeInTheDocument();
    expect(screen.getByText("Category")).toBeInTheDocument();
    expect(screen.getByText("First seen")).toBeInTheDocument();

    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit).toHaveBeenCalledWith({
      "0": {
        "0-0": [
          {
            Species: "",
            Notes: "",
            Count: "",
            Approved: false,
            Category: "",
            "First seen": null,
          },
        ],
      },
    });
  });

  it("supports editing, saving and deleting row records in the grid workflow", async () => {
    const user = userEvent.setup();
    const question = buildGridQuestion();

    renderWithForm({
      ui: <GridInput question={question} />,
      defaultValues: {
        0: {
          "0-0": [{
            Species: "Quokka",
            Notes: "Warm-weather grazers",
            Count: 2,
            Approved: true,
            Category: "Mammal",
            "First seen": "2025-09-01",
          }],
        },
      },
    });

    await user.click(screen.getByRole("button", { name: "Edit" }));
    expect(screen.getByRole("button", { name: "Save" })).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Save" }));
    expect(screen.getByRole("button", { name: "Delete" })).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Delete" }));
    expect(screen.queryByText("Quokka")).not.toBeInTheDocument();
  });

  it("edits textarea grid values via the dialog editor and persists on apply", async () => {
    const user = userEvent.setup();
    const question = buildGridQuestion();
    const onSubmit = vi.fn();

    renderWithForm({
      ui: <GridInput question={question} />,
      onSubmit,
      defaultValues: {
        0: {
          "0-0": [{
            Species: "Quokka",
            Notes: "Initial note",
            Count: 2,
            Approved: true,
            Category: "Mammal",
            "First seen": "2025-09-01",
          }],
        },
      },
    });

    await user.click(screen.getByRole("button", { name: "Edit" }));
    await user.click(screen.getByRole("button", { name: "Edit text" }));

    const dialog = screen.getByRole("dialog", { name: "Notes" });
    const notesInput = within(dialog).getByRole("textbox", { name: "Notes" });
    await user.clear(notesInput);
    await user.type(notesInput, "Updated multiline details for this location");
    await user.click(within(dialog).getByRole("button", { name: "Apply" }));
    await waitFor(() => {
      expect(screen.queryByRole("dialog", { name: "Notes" })).not.toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: "Submit" }));

    const submitted = onSubmit.mock.calls[0][0];
    expect(submitted["0"]["0-0"][0].Notes).toBe("Updated multiline details for this location");
  });

  it("keeps original textarea value when dialog editor is cancelled", async () => {
    const user = userEvent.setup();
    const question = buildGridQuestion();
    const onSubmit = vi.fn();

    renderWithForm({
      ui: <GridInput question={question} />,
      onSubmit,
      defaultValues: {
        0: {
          "0-0": [{
            Species: "Quokka",
            Notes: "Original note",
            Count: 2,
            Approved: true,
            Category: "Mammal",
            "First seen": "2025-09-01",
          }],
        },
      },
    });

    await user.click(screen.getByRole("button", { name: "Edit" }));
    await user.click(screen.getByRole("button", { name: "Edit text" }));

    const dialog = screen.getByRole("dialog", { name: "Notes" });
    const notesInput = within(dialog).getByRole("textbox", { name: "Notes" });
    await user.clear(notesInput);
    await user.type(notesInput, "This change should be discarded");
    await user.click(within(dialog).getByRole("button", { name: "Cancel" }));
    await waitFor(() => {
      expect(screen.queryByRole("dialog", { name: "Notes" })).not.toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: "Submit" }));

    const submitted = onSubmit.mock.calls[0][0];
    expect(submitted["0"]["0-0"][0].Notes).toBe("Original note");
  });

  it("allows cancellation of a newly added row without persisting it", async () => {
    const user = userEvent.setup();
    const question = buildGridQuestion({
      is_required: true,
    });

    renderWithForm({ ui: <GridInput question={question} /> });
    await user.click(screen.getByRole("button", { name: "Add Record" }));

    expect(screen.getByRole("button", { name: "Cancel" })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Cancel" }));
    await user.click(screen.getByRole("button", { name: "Submit" }));

    expect(await screen.findByText("At least one record must be provided.")).toBeInTheDocument();
  });
});
