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
      app_version: "1.0.0",
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

  it("fetchApplications calls correct endpoint", async () => {
    (axios.get as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({ data: [] });

    await ApiManager.fetchApplications();

    const calls = (axios.get as unknown as ReturnType<typeof vi.fn>).mock.calls;
    expect(calls[0][0]).toBe("/applications");
  });

  it("getApplicationAttachments calls correct endpoint with app key", async () => {
    (axios.get as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({ data: [] });

    await ApiManager.getApplicationAttachments("app-123");

    const calls = (axios.get as unknown as ReturnType<typeof vi.fn>).mock.calls;
    expect(calls[0][0]).toBe("/attachments?application_key=app-123");
  });

  it("deleteAttachment calls DELETE on correct endpoint", async () => {
    (axios.delete as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({});

    await ApiManager.deleteAttachment("att-123");

    const calls = (axios.delete as unknown as ReturnType<typeof vi.fn>).mock.calls;
    expect(calls[0][0]).toBe("/attachments/att-123");
  });

  it("renameAttachment sends PATCH with new name", async () => {
    (axios.patch as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({ data: { key: "att-123", name: "new.pdf" } });

    await ApiManager.renameAttachment("att-123", "new.pdf");

    const calls = (axios.patch as unknown as ReturnType<typeof vi.fn>).mock.calls;
    expect(calls[0][0]).toBe("/attachments/att-123");
    expect(calls[0][1]).toEqual({ name: "new.pdf" });
  });

  it("getQuestionnaire calls correct endpoint with questionnaire ID", async () => {
    (axios.get as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({ data: {} });

    await ApiManager.getQuestionnaire(42);

    const calls = (axios.get as unknown as ReturnType<typeof vi.fn>).mock.calls;
    expect(calls[0][0]).toBe("/questionnaires/42");
  });

  it("fetchQuestionnaires calls questionnaires endpoint", async () => {
    (axios.get as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({ data: [] });

    await ApiManager.fetchQuestionnaires();

    const calls = (axios.get as unknown as ReturnType<typeof vi.fn>).mock.calls;
    expect(calls[0][0]).toBe("/questionnaires");
  });

  it("fetchAuthorisationProcesses calls processes endpoint", async () => {
    (axios.get as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({ data: [] });

    await ApiManager.fetchAuthorisationProcesses();

    const calls = (axios.get as unknown as ReturnType<typeof vi.fn>).mock.calls;
    expect(calls[0][0]).toBe("/processes");
  });

  it("updateApplication sends PUT request with document", async () => {
    const doc = { schema_version: "1.0", active_step: 0, steps: [] };
    (axios.put as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({ data: { key: "app-1" } });

    await ApiManager.updateApplication("app-1", doc);

    const calls = (axios.put as unknown as ReturnType<typeof vi.fn>).mock.calls;
    expect(calls[0][0]).toBe("/applications/app-1");
    expect(calls[0][1]).toEqual({ document: doc });
  });

  it("handles API errors and re-throws", async () => {
    const error = new Error("Network error");
    (axios.get as unknown as ReturnType<typeof vi.fn>).mockRejectedValue(error);

    await expect(ApiManager.fetchApplications()).rejects.toBe(error);
  });
});
