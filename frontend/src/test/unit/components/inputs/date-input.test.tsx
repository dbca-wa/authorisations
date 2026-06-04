import dayjs from "dayjs";
import { fireEvent, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { DateInput } from "../../../../components/inputs/date";
import { makeQuestion, renderWithForm } from "./helpers";

vi.mock("@mui/x-date-pickers/DatePicker", () => ({
  DatePicker: ({ label, onChange, slotProps }: {
    label: string;
    onChange: (value: ReturnType<typeof dayjs> | null) => void;
    slotProps: { textField?: { helperText?: string } };
  }) => (
    <div>
      <button type="button" onClick={() => onChange(dayjs("2026-05-14"))}>Pick date</button>
      <span>{label}</span>
      <span>{slotProps?.textField?.helperText}</span>
    </div>
  ),
}));


describe("DateInput", () => {
  it("renders label and helper description", () => {
    const question = makeQuestion({ type: "date", label: "Start date", description: "Pick a date" });

    renderWithForm({ ui: <DateInput question={question} /> });

    expect(screen.getByText("1. Start date")).toBeInTheDocument();
    expect(screen.getByText("Pick a date")).toBeInTheDocument();
  });

  it("stores selected date as YYYY-MM-DD in form state", async () => {
    const question = makeQuestion({ type: "date", label: "Date field" });
    const onSubmit = vi.fn();

    renderWithForm({ ui: <DateInput question={question} />, onSubmit });

    fireEvent.click(screen.getByRole("button", { name: "Pick date" }));
    fireEvent.click(screen.getByRole("button", { name: "Submit" }));

    await waitFor(() => expect(onSubmit).toHaveBeenCalledTimes(1));
    const submitted = onSubmit.mock.calls[0][0];
    expect(JSON.stringify(submitted)).toContain("2026-05-14");
  });
});
