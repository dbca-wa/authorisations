import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { PrivacyStatement } from "../../../../../components/layout/main/PrivacyStatement";


describe("PrivacyStatement", () => {
  it("renders the page heading and accordion triggers", () => {
    render(<PrivacyStatement />);

    expect(screen.getByText("Privacy Statement")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "What information do we collect?" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Information collected automatically" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Contact information" })).toBeInTheDocument();
  });

  it("toggles accordion expanded state when a section heading is clicked", () => {
    render(<PrivacyStatement />);

    const sectionButton = screen.getByRole("button", { name: "How we use your information" });
    expect(sectionButton).toHaveAttribute("aria-expanded", "false");

    fireEvent.click(sectionButton);
    expect(sectionButton).toHaveAttribute("aria-expanded", "true");

    fireEvent.click(sectionButton);
    expect(sectionButton).toHaveAttribute("aria-expanded", "false");
  });

  it("opens contact information accordion and exposes contact links", () => {
    render(<PrivacyStatement />);

    const contactButton = screen.getByRole("button", { name: "Contact information" });
    fireEvent.click(contactButton);

    expect(screen.getByRole("link", { name: "ecoinformatics.admin@dbca.wa.gov.au" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "privacy@dbca.wa.gov.au" })).toBeInTheDocument();
  });
});
