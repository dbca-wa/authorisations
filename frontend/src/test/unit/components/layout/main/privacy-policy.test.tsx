import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { PrivacyPolicy } from "../../../../../components/layout/main/PrivacyPolicy";


describe("PrivacyPolicy", () => {
  it("renders policy heading and privacy contact email", () => {
    render(<PrivacyPolicy />);

    expect(screen.getByText("Privacy Policy")).toBeInTheDocument();
    const emailLink = screen.getByRole("link", { name: "privacy@dbca.wa.gov.au" });
    expect(emailLink).toHaveAttribute("href", "mailto:privacy@dbca.wa.gov.au");
  });
});
