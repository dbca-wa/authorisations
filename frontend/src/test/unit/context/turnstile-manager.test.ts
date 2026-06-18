import { beforeEach, describe, expect, it, vi } from "vitest";

import { ConfigManager } from "../../../context/ConfigManager";
import { TurnstileManager } from "../../../context/TurnstileManager";


type TurnstileApiMock = {
  render: ReturnType<typeof vi.fn>;
  execute: ReturnType<typeof vi.fn>;
  reset: ReturnType<typeof vi.fn>;
  remove: ReturnType<typeof vi.fn>;
  getResponse: ReturnType<typeof vi.fn>;
  isExpired: ReturnType<typeof vi.fn>;
};

const makeApi = (): TurnstileApiMock => ({
  render: vi.fn().mockReturnValue("widget-id"),
  execute: vi.fn(),
  reset: vi.fn(),
  remove: vi.fn(),
  getResponse: vi.fn().mockReturnValue("token"),
  isExpired: vi.fn().mockReturnValue(false),
});


describe("TurnstileManager", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    document.head.innerHTML = "";
    delete (window as unknown as Record<string, unknown>).turnstile;
    (TurnstileManager as unknown as { _api: unknown })._api = null;
    (TurnstileManager as unknown as { scriptPromise: unknown }).scriptPromise = null;
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

  it("loadScript injects script and preconnect, then resolves API on load", async () => {
    const api = makeApi();
    (window as unknown as Record<string, unknown>).turnstile = api;

    const pending = TurnstileManager.loadScript();
    const script = document.getElementById("cloudflare-turnstile-script") as HTMLScriptElement;

    expect(script).toBeTruthy();
    expect(document.querySelector('link[rel="preconnect"][href="https://challenges.cloudflare.com"]')).toBeTruthy();

    script.dispatchEvent(new Event("load"));
    const loaded = await pending;

    expect(loaded).toBe(api);
  });

  it("render passes configured defaults and callback handlers", async () => {
    const api = makeApi();
    (window as unknown as Record<string, unknown>).turnstile = api;

    const pending = TurnstileManager.loadScript();
    const script = document.getElementById("cloudflare-turnstile-script") as HTMLScriptElement;
    script.dispatchEvent(new Event("load"));
    await pending;

    const onSuccess = vi.fn();
    const widgetId = await TurnstileManager.render("container-id", { onSuccess });

    expect(widgetId).toBe("widget-id");
    expect(api.render).toHaveBeenCalledWith(
      "container-id",
      expect.objectContaining({
        sitekey: "site-key",
        theme: "light",
        callback: onSuccess,
      }),
    );
  });

  it("preload swallows load errors without throwing", async () => {
    const loadSpy = vi.spyOn(TurnstileManager, "loadScript").mockRejectedValue(new Error("network"));

    expect(() => TurnstileManager.preload()).not.toThrow();

    await Promise.resolve();
    expect(loadSpy).toHaveBeenCalled();
  });
});
