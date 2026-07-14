import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { EmptyStateComponent } from "../../../../../components/layout/main/EmptyState";


describe("EmptyStateComponent", () => {
  it("renders empty-state title and guidance message", () => {
    render(<EmptyStateComponent />);

    expect(screen.getByText("Nothing to see here")).toBeInTheDocument();
    expect(screen.getByText(/We checked.*There really isn't anything hiding here/)).toBeInTheDocument();
  });
});
