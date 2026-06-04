import { act, renderHook } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { DialogContext } from "../../../context/DialogContext";
import { SnackbarContext } from "../../../context/SnackbarContext";
import { useDialog, useResolvedPromise, useSnackbar } from "../../../context/Hooks";


describe("Hooks", () => {
  it("useDialog throws when provider is missing", () => {
    expect(() => renderHook(() => useDialog())).toThrow("useDialog must be used within a DialogProvider");
  });

  it("useSnackbar throws when provider is missing", () => {
    expect(() => renderHook(() => useSnackbar())).toThrow("useSnackbar must be used within a SnackbarProvider");
  });

  it("useDialog returns context value when provider exists", () => {
    const contextValue = {
      showDialog: () => undefined,
      hideDialog: () => undefined,
    };

    const { result } = renderHook(() => useDialog(), {
      wrapper: ({ children }) => <DialogContext.Provider value={contextValue}>{children}</DialogContext.Provider>,
    });

    expect(result.current).toBe(contextValue);
  });

  it("useResolvedPromise resolves successful deferred values", async () => {
    const promise = Promise.resolve("done");
    const { result } = renderHook(() => useResolvedPromise(promise, "initial"));

    expect(result.current[0]).toBe("initial");
    expect(result.current[1]).toBe(true);

    await act(async () => {
      await promise;
    });

    expect(result.current[0]).toBe("done");
    expect(result.current[1]).toBe(false);
  });

  it("useResolvedPromise falls back to initial value on rejection", async () => {
    const promise = Promise.reject(new Error("boom"));
    const { result } = renderHook(() => useResolvedPromise(promise, ["fallback"]));

    await act(async () => {
      try {
        await promise;
      } catch {
        // expected in test
      }
    });

    expect(result.current[0]).toEqual(["fallback"]);
    expect(result.current[1]).toBe(false);
  });

  it("useSnackbar returns context value when provider exists", () => {
    const contextValue = { showSnackbar: () => undefined };

    const { result } = renderHook(() => useSnackbar(), {
      wrapper: ({ children }) => <SnackbarContext.Provider value={contextValue}>{children}</SnackbarContext.Provider>,
    });

    expect(result.current).toBe(contextValue);
  });
});
