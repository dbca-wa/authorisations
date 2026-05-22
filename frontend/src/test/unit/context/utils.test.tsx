import { isValidElement } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  assert,
  getIconFromFilename,
  handleApiError,
  openNewTab,
  scrollToQuestion,
  scrollToTop,
} from "../../../context/Utils";


describe("Utils", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("returns expected icon classes for known and unknown extensions", () => {
    const pdfIcon = getIconFromFilename("file.PDF");
    const unknownIcon = getIconFromFilename("file.abc");

    if (!isValidElement<{ className?: string }>(pdfIcon) || !isValidElement<{ className?: string }>(unknownIcon)) {
      throw new Error("Expected React elements from getIconFromFilename.");
    }

    expect(pdfIcon.props.className).toContain("vscode-icons--file-type-pdf2");
    expect(unknownIcon.props.className).toContain("flat-color-icons--file");
  });

  it("scrolls resolved question element into view", () => {
    const target = document.createElement("div");
    const scrollIntoView = vi.fn();

    target.id = "q-2.1-3";
    Object.defineProperty(target, "scrollIntoView", {
      value: scrollIntoView,
      configurable: true,
    });
    document.body.appendChild(target);

    try {
      scrollToQuestion({ stepIndex: 2, sectionIndex: 1, questionIndex: 3 });
      expect(scrollIntoView).toHaveBeenCalledWith({ behavior: "smooth", block: "center" });
    } finally {
      target.remove();
    }
  });

  it("scrollToTop delegates to window.scrollTo", () => {
    const spy = vi.spyOn(window, "scrollTo").mockImplementation(() => undefined);

    scrollToTop();

    expect(spy).toHaveBeenCalledWith(0, 0);
  });

  it("openNewTab sets noopener safety and focuses new window", () => {
    const focus = vi.fn();
    const opened: Pick<Window, "opener" | "focus"> = { opener: null, focus };
    const openSpy = vi.spyOn(window, "open").mockReturnValue(opened as unknown as Window);

    openNewTab("/a/1", "window-1");

    expect(openSpy).toHaveBeenCalledWith("/a/1", "window-1", "noopener");
    expect(opened.opener).toBeNull();
    expect(focus).toHaveBeenCalled();
  });

  it("assert throws when condition is false in development", () => {
    expect(() => assert(false, "broken invariant")).toThrow("broken invariant");
  });

  it("handleApiError throws Response with status and message", async () => {
    const error = {
      status: 400,
      response: { statusText: "Bad Request" },
      message: "Validation failed",
    };

    try {
      handleApiError(error as never);
      throw new Error("Expected handleApiError to throw");
    } catch (thrown) {
      expect(thrown).toBeInstanceOf(Response);
      const response = thrown as Response;
      expect(response.status).toBe(400);
      expect(response.statusText).toBe("Bad Request");
    }
  });
});
