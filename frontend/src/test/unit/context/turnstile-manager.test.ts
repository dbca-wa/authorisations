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

const resetTurnstileState = () => {
  document.head.innerHTML = "";
  delete (window as unknown as Record<string, unknown>).turnstile;
  (TurnstileManager as unknown as { _api: unknown })._api = null;
  (TurnstileManager as unknown as { scriptPromise: unknown }).scriptPromise = null;
};

describe("TurnstileManager", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    resetTurnstileState();
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

  describe("getSiteKey", () => {
    it("throws when site key is missing during render", async () => {
      vi.spyOn(ConfigManager, "get").mockReturnValue({
        api_base: "/api",
        csrf_header: "X-CsrfToken",
        csrf_token: "csrf-token",
        app_version: "1.0.0",
        upload_max_size: 1000,
        turnstile_site_key: "",
        upload_mime_types: ["application/pdf"],
      });

      const api = makeApi();
      (window as unknown as Record<string, unknown>).turnstile = api;

      const pending = TurnstileManager.loadScript();
      const script = document.getElementById("cloudflare-turnstile-script") as HTMLScriptElement;
      script.dispatchEvent(new Event("load"));
      await pending;

      // getSiteKey is called during render, not loadScript
      await expect(TurnstileManager.render("container")).rejects.toThrow(
        "Missing Turnstile site key in client config."
      );
    });
  });

  describe("loadScript", () => {
    it("injects script with correct attributes and preconnect link", async () => {
      const api = makeApi();
      (window as unknown as Record<string, unknown>).turnstile = api;

      const pending = TurnstileManager.loadScript();
      const script = document.getElementById("cloudflare-turnstile-script") as HTMLScriptElement;

      expect(script).toBeTruthy();
      expect(script.src).toBe("https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit");
      expect(script.defer).toBe(true);
      expect(script.async).toBe(true);

      const preconnect = document.querySelector<HTMLLinkElement>(
        'link[rel="preconnect"][href="https://challenges.cloudflare.com"]'
      );
      expect(preconnect).toBeTruthy();

      script.dispatchEvent(new Event("load"));
      const loaded = await pending;

      expect(loaded).toBe(api);
    });

    it("returns cached API on second call without re-injecting script", async () => {
      const api = makeApi();
      (window as unknown as Record<string, unknown>).turnstile = api;

      const pending1 = TurnstileManager.loadScript();
      const script = document.getElementById("cloudflare-turnstile-script") as HTMLScriptElement;
      script.dispatchEvent(new Event("load"));
      await pending1;

      // Clear the DOM to verify script isn't re-injected
      document.head.innerHTML = "";

      const loaded2 = await TurnstileManager.loadScript();
      expect(loaded2).toBe(api);
      expect(document.getElementById("cloudflare-turnstile-script")).toBeFalsy();
    });

    it("deduplicates concurrent loadScript calls sharing single promise", async () => {
      const api = makeApi();
      (window as unknown as Record<string, unknown>).turnstile = api;

      const pending1 = TurnstileManager.loadScript();
      const pending2 = TurnstileManager.loadScript();
      const pending3 = TurnstileManager.loadScript();

      const script = document.getElementById("cloudflare-turnstile-script") as HTMLScriptElement;
      script.dispatchEvent(new Event("load"));

      const loaded1 = await pending1;
      const loaded2 = await pending2;
      const loaded3 = await pending3;

      expect(loaded1).toBe(api);
      expect(loaded2).toBe(api);
      expect(loaded3).toBe(api);
      // Only one script element should exist
      expect(document.querySelectorAll('script[id="cloudflare-turnstile-script"]').length).toBe(1);
    });

    it("uses existing script element if already present in DOM", async () => {
      const existingScript = document.createElement("script");
      existingScript.id = "cloudflare-turnstile-script";
      document.head.appendChild(existingScript);

      const api = makeApi();
      (window as unknown as Record<string, unknown>).turnstile = api;

      const pending = TurnstileManager.loadScript();
      existingScript.dispatchEvent(new Event("load"));
      const loaded = await pending;

      expect(loaded).toBe(api);
    });

    it("rejects when script fails to load", async () => {
      const pending = TurnstileManager.loadScript();
      const script = document.getElementById("cloudflare-turnstile-script") as HTMLScriptElement;

      script.dispatchEvent(new Event("error"));

      await expect(pending).rejects.toThrow("Failed to load the Cloudflare Turnstile script.");
    });

    it("rejects when Turnstile API is not exposed on window after script load", async () => {
      const pending = TurnstileManager.loadScript();
      const script = document.getElementById("cloudflare-turnstile-script") as HTMLScriptElement;

      script.dispatchEvent(new Event("load"));

      await expect(pending).rejects.toThrow(
        "Cloudflare Turnstile loaded without exposing the global API."
      );
    });

    it("clears scriptPromise on failure so retries can start fresh", async () => {
      const pending1 = TurnstileManager.loadScript();
      const script = document.getElementById("cloudflare-turnstile-script") as HTMLScriptElement;

      script.dispatchEvent(new Event("error"));

      await expect(pending1).rejects.toThrow();

      // Second call should create a new promise and script
      resetTurnstileState();
      const api = makeApi();
      (window as unknown as Record<string, unknown>).turnstile = api;

      const pending2 = TurnstileManager.loadScript();
      const newScript = document.getElementById("cloudflare-turnstile-script") as HTMLScriptElement;

      expect(newScript).toBeTruthy();
      newScript.dispatchEvent(new Event("load"));
      const loaded = await pending2;
      expect(loaded).toBe(api);
    });
  });

  describe("preload", () => {
    it("starts loading script without blocking caller", () => {
      const api = makeApi();
      (window as unknown as Record<string, unknown>).turnstile = api;

      const result = TurnstileManager.preload();

      expect(result).toBeUndefined();
      expect(document.getElementById("cloudflare-turnstile-script")).toBeTruthy();
    });

    it("swallows errors from failed script load", async () => {
      expect(() => TurnstileManager.preload()).not.toThrow();

      const script = document.getElementById("cloudflare-turnstile-script") as HTMLScriptElement;
      script.dispatchEvent(new Event("error"));

      // Allow error to process and verify no exception escapes
      await new Promise(resolve => setTimeout(resolve, 10));
    });

    it("fire-and-forget does not block on network delays", async () => {
      const api = makeApi();
      (window as unknown as Record<string, unknown>).turnstile = api;

      const startTime = performance.now();
      TurnstileManager.preload();
      const endTime = performance.now();

      expect(endTime - startTime).toBeLessThan(50); // Should return almost immediately
    });
  });

  describe("render", () => {
    it("passes all configured defaults and callback handlers to API", async () => {
      const api = makeApi();
      (window as unknown as Record<string, unknown>).turnstile = api;

      const pending = TurnstileManager.loadScript();
      const script = document.getElementById("cloudflare-turnstile-script") as HTMLScriptElement;
      script.dispatchEvent(new Event("load"));
      await pending;

      const onSuccess = vi.fn();
      const onError = vi.fn();
      const onExpire = vi.fn();

      const widgetId = await TurnstileManager.render("container-id", {
        onSuccess,
        onError,
        onExpire,
      });

      expect(widgetId).toBe("widget-id");
      expect(api.render).toHaveBeenCalledWith(
        "container-id",
        expect.objectContaining({
          sitekey: "site-key",
          theme: "light",
          size: "normal",
          execution: "render",
          appearance: "always",
          callback: onSuccess,
          "error-callback": onError,
          "expired-callback": onExpire,
          retry: "auto",
          "refresh-expired": "auto",
          "refresh-timeout": "auto",
        })
      );
    });

    it("accepts HTMLElement as container", async () => {
      const api = makeApi();
      (window as unknown as Record<string, unknown>).turnstile = api;

      const pending = TurnstileManager.loadScript();
      const script = document.getElementById("cloudflare-turnstile-script") as HTMLScriptElement;
      script.dispatchEvent(new Event("load"));
      await pending;

      const container = document.createElement("div");
      container.id = "my-container";

      await TurnstileManager.render(container);

      expect(api.render).toHaveBeenCalledWith(container, expect.any(Object));
    });

    it("returns widget id from API", async () => {
      const api = makeApi();
      api.render.mockReturnValue("custom-widget-id");
      (window as unknown as Record<string, unknown>).turnstile = api;

      const pending = TurnstileManager.loadScript();
      const script = document.getElementById("cloudflare-turnstile-script") as HTMLScriptElement;
      script.dispatchEvent(new Event("load"));
      await pending;

      const widgetId = await TurnstileManager.render("container");

      expect(widgetId).toBe("custom-widget-id");
    });

    it("handles render with partial callbacks object", async () => {
      const api = makeApi();
      (window as unknown as Record<string, unknown>).turnstile = api;

      const pending = TurnstileManager.loadScript();
      const script = document.getElementById("cloudflare-turnstile-script") as HTMLScriptElement;
      script.dispatchEvent(new Event("load"));
      await pending;

      const onSuccess = vi.fn();

      await TurnstileManager.render("container", { onSuccess });

      expect(api.render).toHaveBeenCalledWith(
        "container",
        expect.objectContaining({
          callback: onSuccess,
          "error-callback": undefined,
          "expired-callback": undefined,
        })
      );
    });

    it("handles render with no callbacks", async () => {
      const api = makeApi();
      (window as unknown as Record<string, unknown>).turnstile = api;

      const pending = TurnstileManager.loadScript();
      const script = document.getElementById("cloudflare-turnstile-script") as HTMLScriptElement;
      script.dispatchEvent(new Event("load"));
      await pending;

      await TurnstileManager.render("container");

      expect(api.render).toHaveBeenCalledWith(
        "container",
        expect.objectContaining({
          callback: undefined,
          "error-callback": undefined,
          "expired-callback": undefined,
        })
      );
    });
  });

  describe("execute", () => {
    it("calls API execute with provided widget id", async () => {
      const api = makeApi();
      (window as unknown as Record<string, unknown>).turnstile = api;

      const pending = TurnstileManager.loadScript();
      const script = document.getElementById("cloudflare-turnstile-script") as HTMLScriptElement;
      script.dispatchEvent(new Event("load"));
      await pending;

      await TurnstileManager.execute("widget-id");

      expect(api.execute).toHaveBeenCalledWith("widget-id");
    });

    it("calls API execute without arguments when not provided", async () => {
      const api = makeApi();
      (window as unknown as Record<string, unknown>).turnstile = api;

      const pending = TurnstileManager.loadScript();
      const script = document.getElementById("cloudflare-turnstile-script") as HTMLScriptElement;
      script.dispatchEvent(new Event("load"));
      await pending;

      await TurnstileManager.execute();

      expect(api.execute).toHaveBeenCalledWith(undefined);
    });
  });

  describe("getResponse", () => {
    it("returns token from API", async () => {
      const api = makeApi();
      api.getResponse.mockReturnValue("test-token-123");
      (window as unknown as Record<string, unknown>).turnstile = api;

      const pending = TurnstileManager.loadScript();
      const script = document.getElementById("cloudflare-turnstile-script") as HTMLScriptElement;
      script.dispatchEvent(new Event("load"));
      await pending;

      const token = await TurnstileManager.getResponse("widget-id");

      expect(token).toBe("test-token-123");
      expect(api.getResponse).toHaveBeenCalledWith("widget-id");
    });

    it("calls API getResponse without arguments when not provided", async () => {
      const api = makeApi();
      (window as unknown as Record<string, unknown>).turnstile = api;

      const pending = TurnstileManager.loadScript();
      const script = document.getElementById("cloudflare-turnstile-script") as HTMLScriptElement;
      script.dispatchEvent(new Event("load"));
      await pending;

      await TurnstileManager.getResponse();

      expect(api.getResponse).toHaveBeenCalledWith(undefined);
    });
  });

  describe("isExpired", () => {
    it("returns expiration status from API", async () => {
      const api = makeApi();
      api.isExpired.mockReturnValue(true);
      (window as unknown as Record<string, unknown>).turnstile = api;

      const pending = TurnstileManager.loadScript();
      const script = document.getElementById("cloudflare-turnstile-script") as HTMLScriptElement;
      script.dispatchEvent(new Event("load"));
      await pending;

      const expired = await TurnstileManager.isExpired("widget-id");

      expect(expired).toBe(true);
      expect(api.isExpired).toHaveBeenCalledWith("widget-id");
    });

    it("handles multiple widget ids correctly", async () => {
      const api = makeApi();
      api.isExpired.mockImplementation((widgetId) => widgetId === "widget-1");
      (window as unknown as Record<string, unknown>).turnstile = api;

      const pending = TurnstileManager.loadScript();
      const script = document.getElementById("cloudflare-turnstile-script") as HTMLScriptElement;
      script.dispatchEvent(new Event("load"));
      await pending;

      const expired1 = await TurnstileManager.isExpired("widget-1");
      const expired2 = await TurnstileManager.isExpired("widget-2");

      expect(expired1).toBe(true);
      expect(expired2).toBe(false);
    });
  });

  describe("reset", () => {
    it("calls API reset with provided widget id", async () => {
      const api = makeApi();
      (window as unknown as Record<string, unknown>).turnstile = api;

      const pending = TurnstileManager.loadScript();
      const script = document.getElementById("cloudflare-turnstile-script") as HTMLScriptElement;
      script.dispatchEvent(new Event("load"));
      await pending;

      await TurnstileManager.reset("widget-id");

      expect(api.reset).toHaveBeenCalledWith("widget-id");
    });

    it("calls API reset without arguments when not provided", async () => {
      const api = makeApi();
      (window as unknown as Record<string, unknown>).turnstile = api;

      const pending = TurnstileManager.loadScript();
      const script = document.getElementById("cloudflare-turnstile-script") as HTMLScriptElement;
      script.dispatchEvent(new Event("load"));
      await pending;

      await TurnstileManager.reset();

      expect(api.reset).toHaveBeenCalledWith(undefined);
    });
  });

  describe("remove", () => {
    it("calls API remove with provided widget id", async () => {
      const api = makeApi();
      (window as unknown as Record<string, unknown>).turnstile = api;

      const pending = TurnstileManager.loadScript();
      const script = document.getElementById("cloudflare-turnstile-script") as HTMLScriptElement;
      script.dispatchEvent(new Event("load"));
      await pending;

      await TurnstileManager.remove("widget-id");

      expect(api.remove).toHaveBeenCalledWith("widget-id");
    });

    it("calls API remove without arguments when not provided", async () => {
      const api = makeApi();
      (window as unknown as Record<string, unknown>).turnstile = api;

      const pending = TurnstileManager.loadScript();
      const script = document.getElementById("cloudflare-turnstile-script") as HTMLScriptElement;
      script.dispatchEvent(new Event("load"));
      await pending;

      await TurnstileManager.remove();

      expect(api.remove).toHaveBeenCalledWith(undefined);
    });
  });

  describe("ensurePreconnect", () => {
    it("adds preconnect link when not present", async () => {
      const api = makeApi();
      (window as unknown as Record<string, unknown>).turnstile = api;

      const pending = TurnstileManager.loadScript();
      const script = document.getElementById("cloudflare-turnstile-script") as HTMLScriptElement;
      script.dispatchEvent(new Event("load"));
      await pending;

      const preconnect = document.querySelector<HTMLLinkElement>(
        'link[rel="preconnect"][href="https://challenges.cloudflare.com"]'
      );

      expect(preconnect).toBeTruthy();
      expect(preconnect?.rel).toBe("preconnect");
    });

    it("does not add duplicate preconnect links on multiple loadScript calls", async () => {
      const api = makeApi();
      (window as unknown as Record<string, unknown>).turnstile = api;

      const pending1 = TurnstileManager.loadScript();
      const script1 = document.getElementById("cloudflare-turnstile-script") as HTMLScriptElement;
      script1.dispatchEvent(new Event("load"));
      await pending1;

      const countAfterFirst = document.querySelectorAll(
        'link[rel="preconnect"][href="https://challenges.cloudflare.com"]'
      ).length;

      const countAfterSecond = document.querySelectorAll(
        'link[rel="preconnect"][href="https://challenges.cloudflare.com"]'
      ).length;

      expect(countAfterFirst).toBe(1);
      expect(countAfterSecond).toBe(1);
    });
  });

  describe("error handling and edge cases", () => {
    it("handles multiple concurrent API operations after single loadScript", async () => {
      const api = makeApi();
      api.getResponse.mockReturnValue("token");
      api.isExpired.mockReturnValue(false);
      (window as unknown as Record<string, unknown>).turnstile = api;

      const pending = TurnstileManager.loadScript();
      const script = document.getElementById("cloudflare-turnstile-script") as HTMLScriptElement;
      script.dispatchEvent(new Event("load"));
      await pending;

      const results = await Promise.all([
        TurnstileManager.getResponse("w1"),
        TurnstileManager.isExpired("w1"),
        TurnstileManager.render("container", { onSuccess: vi.fn() }),
        TurnstileManager.reset("w1"),
      ]);

      expect(results).toHaveLength(4);
      expect(api.getResponse).toHaveBeenCalled();
      expect(api.isExpired).toHaveBeenCalled();
      expect(api.render).toHaveBeenCalled();
      expect(api.reset).toHaveBeenCalled();
    });

    it("renders multiple widgets in sequence", async () => {
      const api = makeApi();
      api.render.mockReturnValueOnce("widget-1").mockReturnValueOnce("widget-2");
      (window as unknown as Record<string, unknown>).turnstile = api;

      const pending = TurnstileManager.loadScript();
      const script = document.getElementById("cloudflare-turnstile-script") as HTMLScriptElement;
      script.dispatchEvent(new Event("load"));
      await pending;

      const id1 = await TurnstileManager.render("container-1");
      const id2 = await TurnstileManager.render("container-2");

      expect(id1).toBe("widget-1");
      expect(id2).toBe("widget-2");
      expect(api.render).toHaveBeenCalledTimes(2);
    });

    it("handles null or undefined sitekey in getSiteKey gracefully", async () => {
      vi.spyOn(ConfigManager, "get").mockReturnValue({
        api_base: "/api",
        csrf_header: "X-CsrfToken",
        csrf_token: "csrf-token",
        app_version: "1.0.0",
        upload_max_size: 1000,
        turnstile_site_key: null as unknown as string,
        upload_mime_types: ["application/pdf"],
      });

      const api = makeApi();
      (window as unknown as Record<string, unknown>).turnstile = api;

      const pending = TurnstileManager.loadScript();
      const script = document.getElementById("cloudflare-turnstile-script") as HTMLScriptElement;
      script.dispatchEvent(new Event("load"));
      await pending;

      // getSiteKey is called during render
      await expect(TurnstileManager.render("container")).rejects.toThrow(
        "Missing Turnstile site key in client config."
      );
    });

    it("scripts listeners resolve immediately if _api already cached", async () => {
      const api = makeApi();
      (window as unknown as Record<string, unknown>).turnstile = api;

      // First load
      let pending = TurnstileManager.loadScript();
      const script1 = document.getElementById("cloudflare-turnstile-script") as HTMLScriptElement;
      script1.dispatchEvent(new Event("load"));
      await pending;

      // Second load with cached _api
      pending = TurnstileManager.loadScript();
      const result = await pending;

      expect(result).toBe(api);
    });

    it("callback integration with NewApplication context", async () => {
      const api = makeApi();
      (window as unknown as Record<string, unknown>).turnstile = api;

      const pending = TurnstileManager.loadScript();
      const script = document.getElementById("cloudflare-turnstile-script") as HTMLScriptElement;
      script.dispatchEvent(new Event("load"));
      await pending;

      const onSuccessCb = vi.fn();
      const onErrorCb = vi.fn();
      const onExpireCb = vi.fn();

      // Simulate PrivacyConsentDialogContent workflow
      const callbacksRef = {
        onSuccess: onSuccessCb,
        onError: onErrorCb,
        onExpire: onExpireCb,
      };

      await TurnstileManager.render("turnstile-container", callbacksRef);

      // Verify callbacks are passed through
      const capturedOptions = (api.render as ReturnType<typeof vi.fn>).mock.calls[0][1];
      expect(capturedOptions.callback).toBe(onSuccessCb);
      expect(capturedOptions["error-callback"]).toBe(onErrorCb);
      expect(capturedOptions["expired-callback"]).toBe(onExpireCb);
    });
  });
});
