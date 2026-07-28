import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AttachmentsDialogContent } from "../../../../../components/layout/main/ReviewCard";
import * as HooksModule from "../../../../../context/Hooks";
import type {
  IApplicationAttachment,
  IApplicationData,
} from "../../../../../context/types/Application";

const mockApp = { key: "app-key-xyz", internal_id: "s40-1" } as unknown as IApplicationData;

vi.mock("../../../../../components/Common", () => ({
  FileAttachmentList: ({ attachments }: { attachments: IApplicationAttachment[] }) => (
    <div>
      {attachments.map((a: IApplicationAttachment) => (
        <div key={a.key}>{a.name}</div>
      ))}
    </div>
  ),
}));

vi.mock("../../../../../context/ApiManager", () => ({
  ApiManager: {
    getApplicationAttachments: vi.fn(() => Promise.resolve([])),
  },
}));

describe("AttachmentsDialogContent", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders empty state when there are no attachments", () => {
    // Mock useResolvedPromise to return empty and not loading
    vi.spyOn(HooksModule, "useResolvedPromise").mockReturnValue([[], false] as unknown as [IApplicationAttachment[], boolean]);

    render(<AttachmentsDialogContent application={mockApp} />);

    expect(screen.getByText("Nothing to see here")).toBeInTheDocument();
  });

  it("renders attachments when present", () => {
    vi.spyOn(HooksModule, "useResolvedPromise").mockReturnValue([
      [
        { key: "a1", name: "file-one.txt", application_key: "app-key-xyz", question: "0-0", created_at: "", download_url: "" },
        { key: "a2", name: "file-two.pdf", application_key: "app-key-xyz", question: "0-0", created_at: "", download_url: "" },
      ],
      false,
    ] as unknown as [IApplicationAttachment[], boolean]);

    render(<AttachmentsDialogContent application={mockApp} />);

    expect(screen.getByText("file-one.txt")).toBeInTheDocument();
    expect(screen.getByText("file-two.pdf")).toBeInTheDocument();
  });
});
