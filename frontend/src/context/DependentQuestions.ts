import { Question, type IQuestion } from "./types/Questionnaire";

export type DependentQuestionMap = Record<string, { parentKey: string }>;

/**
 * Build a map of dependent question keys to their parent question keys for one section.
 *
 * This preserves the existing same-section walkback behaviour used by the form editor:
 * `dependent_step` points to a prior question index within the current section only.
 */
export const computeDependentQuestionMap = (
    questions: IQuestion[],
    stepIndex: number,
    sectionIndex: number,
): DependentQuestionMap => {
    const map: DependentQuestionMap = {};

    questions.forEach((questionObj, questionIndex) => {
        const question = new Question(questionObj, {
            step: stepIndex,
            section: sectionIndex,
            question: questionIndex,
        });

        const walkback = question.o.config?.dependent_step;
        if (walkback && questionIndex - walkback >= 0) {
            const parentQuestion = new Question(
                questions[questionIndex - walkback],
                {
                    step: stepIndex,
                    section: sectionIndex,
                    question: questionIndex - walkback,
                },
            );
            map[question.key] = { parentKey: parentQuestion.key };
        }
    });

    return map;
};

/**
 * Return whether a parent answer value should reveal its dependent questions.
 *
 * Business rule: `"no"` (case-insensitive) is treated as falsy even though it is a non-empty string.
 */
export const isDependentQuestionParentValueTruthy = (value: unknown): boolean => {
    if (typeof value === "string") {
        return value.trim() !== "" && value.trim().toLowerCase() !== "no";
    }

    return Boolean(value);
};

/**
 * Compute visibility for dependent questions from a dependency map and answer values.
 *
 * Non-dependent questions are not included in the returned map and should default to visible.
 * Dependency chains are resolved recursively so hidden parents hide all descendants.
 */
export const computeDependentQuestionVisibilityMap = ({
    dependentQuestionMap,
    answerValuesByQuestionKey,
}: {
    dependentQuestionMap: DependentQuestionMap;
    answerValuesByQuestionKey: Record<string, unknown>;
}): Record<string, boolean> => {
    const visibilityCache: Record<string, boolean> = {};

    const computeVisibility = (questionKey: string): boolean => {
        if (Object.hasOwn(visibilityCache, questionKey)) {
            return visibilityCache[questionKey];
        }

        const dependencyInfo = dependentQuestionMap[questionKey];
        if (!dependencyInfo) {
            visibilityCache[questionKey] = true;
            return true;
        }

        const parentKey = dependencyInfo.parentKey;
        const parentValue = answerValuesByQuestionKey[parentKey];
        const isParentVisible = computeVisibility(parentKey);
        const isParentTruthy = isDependentQuestionParentValueTruthy(parentValue);

        visibilityCache[questionKey] = isParentVisible && isParentTruthy;
        return visibilityCache[questionKey];
    };

    Object.keys(dependentQuestionMap).forEach((questionKey) => {
        computeVisibility(questionKey);
    });

    return visibilityCache;
};
