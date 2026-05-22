import axios from "axios";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiManager } from "../../../context/ApiManager";
import { ConfigManager } from "../../../context/ConfigManager";

vi.mock("axios", () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}));


describe("ApiManager", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(ConfigManager, "get").mockReturnValue({
      api_base: "/api",
      csrf_header: "X-CsrfToken",
      csrf_token: "csrf-token",
      upload_max_size: 1000,
      turnstile_site_key: "site-key",
      upload_mime_types: ["application/pdf"],
    });
  });

  it("maps createApplication payload to backend snake_case keys", async () => {
    (axios.post as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({ data: { key: "app-key" } });

    await ApiManager.createApplication({
      processSlug: "s40",
      questionnaireId: 5,
      questionnaireCode: "new",
      questionnaireVersion: 2,
      privacyConsentAgreed: true,
      turnstileToken: "ts-token",
    });

    const [url, payload, config] = (axios.post as unknown as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(url).toBe("/applications");
    expect(payload).toEqual({
      process_slug: "s40",
      questionnaire_id: 5,
      questionnaire_code: "new",
      questionnaire_version: 2,
      privacy_consent_agreed: true,
      turnstile_token: "ts-token",
    });
    expect(config.baseURL).toBe("/api");
    expect(config.headers["X-CsrfToken"]).toBe("csrf-token");
  });

  it("submitApplication sends SUBMITTED patch with turnstile token", async () => {
    (axios.patch as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({ data: { status: "SUBMITTED" } });

    await ApiManager.submitApplication("app-1", "token-1");

    const [url, payload] = (axios.patch as unknown as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(url).toBe("/applications/app-1");
    expect(payload).toEqual({ status: "SUBMITTED", turnstile_token: "token-1" });
  });

  it("uploadAttachment uses multipart and forwards progress/signal", async () => {
    (axios.post as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({ data: { key: "att-1" } });
    const signal = new AbortController().signal;
    const callback = vi.fn();

    await ApiManager.uploadAttachment({
      appKey: "app-1",
      name: "Evidence.pdf",
      question: "0.0-0",
      file: new File(["pdf"], "evidence.pdf", { type: "application/pdf" }),
      signal,
      callback,
    });

    const [url, formData, config] = (axios.post as unknown as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(url).toBe("/attachments");
    expect(formData).toBeInstanceOf(FormData);
    expect(config.headers["Content-Type"]).toBe("multipart/form-data");
    expect(config.signal).toBe(signal);
    expect(config.onUploadProgress).toBe(callback);
  });

  it("fetchAssessmentApplications targets assessment endpoint", async () => {
    (axios.get as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({ data: [] });

    await ApiManager.fetchAssessmentApplications();

    expect((axios.get as unknown as ReturnType<typeof vi.fn>).mock.calls[0][0]).toBe("/assessment");
  });
});
