import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { EmptyStateComponent } from "../../../../../components/layout/main/EmptyState";


describe("EmptyStateComponent", () => {
  it("renders empty-state title and guidance message", () => {
    render(<EmptyStateComponent />);

    expect(screen.getByText("No items found")).toBeInTheDocument();
    expect(screen.getByText("It looks like there's nothing here yet.")).toBeInTheDocument();
  });
});
