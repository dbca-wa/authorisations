import { beforeEach, describe, expect, it } from "vitest";

import { LocalStorage } from "../../../context/LocalStorage";


describe("LocalStorage", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("prefixes keys with auth_ when setting and getting values", () => {
    LocalStorage.setValue("sort-order", "newest");

    expect(window.localStorage.getItem("auth_sort-order")).toBe("\"newest\"");
    expect(LocalStorage.getValue<string>("sort-order")).toBe("newest");
  });

  it("stores and retrieves form state by application key", () => {
    const documentState = {
      schema_version: "2025.07-1",
      active_step: 0,
      steps: [{ is_valid: null, answers: {} }],
    };

    LocalStorage.setFormState("app-1", documentState);

    expect(LocalStorage.getFormState("app-1")).toEqual(documentState);
  });

  it("returns null for missing values", () => {
    expect(LocalStorage.getValue<string>("missing")).toBeNull();
  });
});
