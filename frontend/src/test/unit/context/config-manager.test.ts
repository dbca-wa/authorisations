import { beforeEach, describe, expect, it, vi } from "vitest";

import { ConfigManager } from "../../../context/ConfigManager";


describe("ConfigManager", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    document.body.innerHTML = "";
    (ConfigManager as unknown as { _config: unknown })._config = null;
  });

  it("reads and decodes base64 config from #config script tag", () => {
    const configPayload = {
      api_base: "/api",
      csrf_header: "X-CsrfToken",
      csrf_token: "token-123",
      app_version: "1.0.0",
      upload_max_size: 1024,
      turnstile_site_key: "site-key",
      upload_mime_types: ["application/pdf"],
    };
    const encoded = btoa(JSON.stringify(configPayload));
    const script = document.createElement("script");
    script.id = "config";
    script.textContent = JSON.stringify(encoded);
    document.body.appendChild(script);

    const config = ConfigManager.get();

    expect(config).toEqual(configPayload);
  });

  it("returns clones so consumers cannot mutate cached config", () => {
    const configPayload = {
      api_base: "/api",
      csrf_header: "X-CsrfToken",
      csrf_token: "token-123",
      app_version: "1.0.0",
      upload_max_size: 1024,
      turnstile_site_key: null,
      upload_mime_types: ["application/pdf"],
    };
    const encoded = btoa(JSON.stringify(configPayload));
    const script = document.createElement("script");
    script.id = "config";
    script.textContent = JSON.stringify(encoded);
    document.body.appendChild(script);

    const first = ConfigManager.get();
    first.api_base = "/changed";

    const second = ConfigManager.get();

    expect(second.api_base).toBe("/api");
  });

  it("throws when config tag is missing", () => {
    expect(() => ConfigManager.get()).toThrow("Config data not found in the document.");
  });
});
