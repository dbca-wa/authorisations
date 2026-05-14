import { beforeEach, describe, expect, it, vi } from "vitest";

import { makeApplication, makeProcess, makeQuestionnaire } from "../fixtures";

const { apiMocks } = vi.hoisted(() => ({
  apiMocks: {
    fetchAuthorisationProcesses: vi.fn(),
    fetchQuestionnaires: vi.fn(),
    fetchApplications: vi.fn(),
    fetchAssessmentApplications: vi.fn(),
    getApplication: vi.fn(),
    getQuestionnaire: vi.fn(),
    getApplicationAttachments: vi.fn(),
  },
}));

vi.mock("../../../context/ApiManager", () => ({
  ApiManager: apiMocks,
}));

vi.mock("../../../context/Utils", async () => {
  const actual = await vi.importActual<typeof import("../../../context/Utils")>("../../../context/Utils");
  return {
    ...actual,
    handleApiError: (error: unknown) => {
      throw error;
    },
  };
});

import { ROUTES } from "../../../router";


describe("router contracts", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("assessment route condition shows only when at least one process is reviewable", () => {
    const assessmentRoute = ROUTES.find((route) => route.path === "/assessment");

    expect(assessmentRoute?.condition?.([makeProcess({ can_review: false })])).toBe(false);
    expect(assessmentRoute?.condition?.([makeProcess({ can_review: true })])).toBe(true);
  });

  it("my-applications loader requests processes and applications only", async () => {
    apiMocks.fetchAuthorisationProcesses.mockResolvedValue([makeProcess()]);
    apiMocks.fetchApplications.mockResolvedValue([makeApplication()]);

    const route = ROUTES.find((currentRoute) => currentRoute.path === "/my-applications");
    const loaded = await route!.loader!({} as never);

    expect(apiMocks.fetchAuthorisationProcesses).toHaveBeenCalledTimes(1);
    expect(apiMocks.fetchApplications).toHaveBeenCalledTimes(1);
    expect(apiMocks.fetchQuestionnaires).not.toHaveBeenCalled();
    expect(loaded.processes).toHaveLength(1);
    await expect(loaded.applications).resolves.toHaveLength(1);
  });

  it("new-application loader requests processes and questionnaires only", async () => {
    apiMocks.fetchAuthorisationProcesses.mockResolvedValue([makeProcess()]);
    apiMocks.fetchQuestionnaires.mockResolvedValue([makeQuestionnaire()]);

    const route = ROUTES.find((currentRoute) => currentRoute.path === "/new-application");
    const loaded = await route!.loader!({} as never);

    expect(apiMocks.fetchAuthorisationProcesses).toHaveBeenCalledTimes(1);
    expect(apiMocks.fetchQuestionnaires).toHaveBeenCalledTimes(1);
    expect(apiMocks.fetchApplications).not.toHaveBeenCalled();
    await expect(loaded.questionnaires).resolves.toHaveLength(1);
  });

  it("assessment loader requests processes and assessment queue", async () => {
    apiMocks.fetchAuthorisationProcesses.mockResolvedValue([makeProcess({ can_review: true })]);
    apiMocks.fetchAssessmentApplications.mockResolvedValue([makeApplication()]);

    const route = ROUTES.find((currentRoute) => currentRoute.path === "/assessment");
    const loaded = await route!.loader!({} as never);

    expect(apiMocks.fetchAuthorisationProcesses).toHaveBeenCalledTimes(1);
    expect(apiMocks.fetchAssessmentApplications).toHaveBeenCalledTimes(1);
    await expect(loaded.applications).resolves.toHaveLength(1);
  });
});
