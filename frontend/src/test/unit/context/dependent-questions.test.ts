import { describe, expect, it } from "vitest";

import {
  computeDependentQuestionMap,
  computeDependentQuestionVisibilityMap,
  isDependentQuestionParentValueTruthy,
} from "../../../context/DependentQuestions";

import type { IQuestion } from "../../../context/types/Questionnaire";

/**
 * Build a minimal text question fixture with optional dependent-step config.
 */
const makeQuestion = (label: string, dependentStep?: number): IQuestion => ({
  label,
  type: "text",
  is_required: false,
  config: dependentStep ? { dependent_step: dependentStep } : undefined,
});

describe("DependentQuestions utilities", () => {
  it("computes dependent parent mappings using same-section walkback offsets", () => {
    const questions: IQuestion[] = [
      makeQuestion("Q1"),
      makeQuestion("Q2", 1),
      makeQuestion("Q3", 2),
      makeQuestion("Q4", 1),
    ];

    const result = computeDependentQuestionMap(questions, 0, 0);

    expect(result).toEqual({
      "0.0-1": { parentKey: "0.0-0" },
      "0.0-2": { parentKey: "0.0-0" },
      "0.0-3": { parentKey: "0.0-2" },
    });
  });

  it("treats string 'no' as falsy regardless of case", () => {
    expect(isDependentQuestionParentValueTruthy("no")).toBe(false);
    expect(isDependentQuestionParentValueTruthy("No")).toBe(false);
    expect(isDependentQuestionParentValueTruthy("nO")).toBe(false);
    expect(isDependentQuestionParentValueTruthy("NO")).toBe(false);
    expect(isDependentQuestionParentValueTruthy("yes")).toBe(true);
  });

  it("resolves transitive visibility through dependent question chains", () => {
    const dependentQuestionMap = {
      "0.0-1": { parentKey: "0.0-0" },
      "0.0-2": { parentKey: "0.0-1" },
    };

    const hiddenResult = computeDependentQuestionVisibilityMap({
      dependentQuestionMap,
      answerValuesByQuestionKey: { "0.0-0": "NO", "0.0-1": "filled" },
    });
    expect(hiddenResult["0.0-1"]).toBe(false);
    expect(hiddenResult["0.0-2"]).toBe(false);

    const visibleResult = computeDependentQuestionVisibilityMap({
      dependentQuestionMap,
      answerValuesByQuestionKey: { "0.0-0": "yes", "0.0-1": "filled" },
    });
    expect(visibleResult["0.0-1"]).toBe(true);
    expect(visibleResult["0.0-2"]).toBe(true);
  });
});
