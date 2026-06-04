import { ConfigManager } from "./ConfigManager";

export type TurnstileContainer = string | HTMLElement;
export type TurnstileWidgetId = string;

interface TurnstileApiRenderOptions {
    sitekey: string;
    theme?: "auto" | "light" | "dark";
    size?: "normal" | "flexible" | "compact";
    execution?: "render" | "execute";
    appearance?: "always" | "execute" | "interaction-only";
    callback?: (token: string) => void;
    "error-callback"?: () => void;
    "expired-callback"?: () => void;
    retry?: "auto" | "never";
    "refresh-expired"?: "auto" | "manual" | "never";
    "refresh-timeout"?: "auto" | "manual" | "never";
}

interface TurnstileRenderCallbacks {
    onSuccess?: (token: string) => void;
    onError?: () => void;
    onExpire?: () => void;
}

interface TurnstileApi {
    render(container: TurnstileContainer, options: TurnstileApiRenderOptions): TurnstileWidgetId;
    execute(containerOrWidgetId?: TurnstileContainer | TurnstileWidgetId): void;
    reset(widgetId?: TurnstileWidgetId): void;
    remove(widgetId?: TurnstileWidgetId): void;
    getResponse(widgetId?: TurnstileWidgetId): string;
    isExpired(widgetId?: TurnstileWidgetId): boolean;
}

/**
 * Manages Cloudflare Turnstile script loading and explicit widget lifecycle operations for the SPA.
 */
export class TurnstileManager {
    private static readonly SCRIPT_ID = "cloudflare-turnstile-script";
    private static readonly SCRIPT_SRC = "https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit";
    private static readonly PRECONNECT_HREF = "https://challenges.cloudflare.com";
    // Cached API reference populated the first time the script loads successfully.
    private static _api: TurnstileApi | null = null;
    private static scriptPromise: Promise<TurnstileApi> | null = null;

    private constructor() {
        // Private constructor prevents accidental instantiation of this static utility.
    }

    /**
     * Returns the configured Turnstile site key from the backend-provided client config.
     */
    private static getSiteKey(): string {
        const siteKey = ConfigManager.get().turnstile_site_key;

        if (!siteKey) {
            throw new Error("Missing Turnstile site key in client config.");
        }

        return siteKey;
    }

    /**
     * Ensures the Cloudflare Turnstile script has been added and the API is ready to use.
     */
    public static async loadScript(): Promise<TurnstileApi> {
        // Fast path: script already loaded and API captured.
        if (this._api) {
            return this._api;
        }

        if (this.scriptPromise) {
            return this.scriptPromise;
        }

        // Add a preconnect hint once so the browser can warm up the Turnstile origin.
        this.ensurePreconnect();

        this.scriptPromise = new Promise<TurnstileApi>((resolve, reject) => {
            const existingScript = document.getElementById(this.SCRIPT_ID) as HTMLScriptElement | null;

            if (existingScript) {
                this.attachScriptListeners(existingScript, resolve, reject);
                return;
            }

            const script = document.createElement("script");
            script.id = this.SCRIPT_ID;
            script.src = this.SCRIPT_SRC;
            script.defer = true;
            script.async = true;

            this.attachScriptListeners(script, resolve, reject);
            document.head.appendChild(script);
        }).catch((error) => {
            // Clear the cached promise after a failure so a later retry can start fresh.
            this.scriptPromise = null;
            throw error;
        });

        return this.scriptPromise;
    }

    /**
     * Starts loading the Cloudflare Turnstile script without rendering a widget.
     * Call this as early as possible (e.g. on page load) so the script is ready
     * before the user reaches a protected form.
     */
    public static preload(): void {
        // Fire-and-forget: we don't await so callers aren't blocked.
        // Errors during preload are expected to surface again when render() is called.
        this.loadScript().catch(() => { /* intentionally swallowed; render() will re-throw */ });
    }

    /**
     * Renders a Turnstile widget explicitly into the supplied container and returns its widget id.
     */
    public static async render(
        container: TurnstileContainer,
        callbacks?: TurnstileRenderCallbacks,
    ): Promise<TurnstileWidgetId> {
        const api = await this.loadScript();
        const renderOptions = this.toApiRenderOptions(callbacks);

        return api.render(container, renderOptions);
    }

    /**
     * Executes a widget when using execution mode set to execute.
     */
    public static async execute(containerOrWidgetId?: TurnstileContainer | TurnstileWidgetId): Promise<void> {
        const api = await this.loadScript();
        api.execute(containerOrWidgetId);
    }

    /**
     * Returns the current response token for a widget, or an empty string if none is available.
     */
    public static async getResponse(widgetId?: TurnstileWidgetId): Promise<string> {
        const api = await this.loadScript();
        return api.getResponse(widgetId);
    }

    /**
     * Reports whether the widget currently holds an expired token.
     */
    public static async isExpired(widgetId?: TurnstileWidgetId): Promise<boolean> {
        const api = await this.loadScript();
        return api.isExpired(widgetId);
    }

    /**
     * Resets a widget so it can issue a fresh token after expiry or failure.
     */
    public static async reset(widgetId?: TurnstileWidgetId): Promise<void> {
        const api = await this.loadScript();
        api.reset(widgetId);
    }

    /**
     * Removes a widget and all related DOM created by Turnstile.
     */
    public static async remove(widgetId?: TurnstileWidgetId): Promise<void> {
        const api = await this.loadScript();
        api.remove(widgetId);
    }

    /**
     * Adds a preconnect resource hint for the Turnstile origin when it is not already present.
     */
    private static ensurePreconnect(): void {
        const existingLink = document.querySelector<HTMLLinkElement>(`link[rel="preconnect"][href="${this.PRECONNECT_HREF}"]`);

        if (existingLink) {
            return;
        }

        const preconnect = document.createElement("link");
        preconnect.rel = "preconnect";
        preconnect.href = this.PRECONNECT_HREF;
        document.head.appendChild(preconnect);
    }

    /**
     * Wires load and error listeners to a script element so callers can await API readiness safely.
     */
    private static attachScriptListeners(
        script: HTMLScriptElement,
        resolve: (api: TurnstileApi) => void,
        reject: (reason?: unknown) => void,
    ): void {
        const handleLoad = () => {
            // Read window.turnstile exactly once at load time, then store it in our private field.
            // After this point, all internal code uses this._api and never touches window again.
            const api = (window as unknown as Record<string, unknown>).turnstile as TurnstileApi | undefined;

            if (!api) {
                reject(new Error("Cloudflare Turnstile loaded without exposing the global API."));
                return;
            }

            this._api = api;
            resolve(api);
        };

        const handleError = () => {
            reject(new Error("Failed to load the Cloudflare Turnstile script."));
        };

        // Fast path: API already captured from a prior load.
        if (this._api) {
            resolve(this._api);
            return;
        }

        script.addEventListener("load", handleLoad, { once: true });
        script.addEventListener("error", handleError, { once: true });
    }

    /**
     * Builds the API render options using only hardcoded manager defaults.
     */
    private static toApiRenderOptions(
        callbacks?: TurnstileRenderCallbacks,
    ): TurnstileApiRenderOptions {
        return {
            sitekey: this.getSiteKey(),
            theme: "light",
            size: "normal",
            execution: "render",
            appearance: "always",
            callback: callbacks?.onSuccess,
            "error-callback": callbacks?.onError,
            "expired-callback": callbacks?.onExpire,
            retry: "auto",
            "refresh-expired": "auto",
            "refresh-timeout": "auto",
        };
    }
}
