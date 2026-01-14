// Utility for follow-up question visibility logic
// Simple: a follow-up is visible if its parent is visible and has a truthy value

import { Question } from '../../../context/types/Questionnaire';

/**
 * Build a map of follow-up question key -> parent question key
 * @param questions Section questions array
 * @param stepIndex Step index
 * @param sectionIndex Section index
 * @param followupObj Mapping of question key to walkback offset
 */
export const computeFollowupMap = (
    questions: any[],
    stepIndex: number,
    sectionIndex: number,
    followupObj: Record<string, number>
) => {
    const map: Record<string, { parentKey: string }> = {};
    questions.forEach((qObj, qIndex) => {
        const question = new Question(qObj, {
            step: stepIndex,
            section: sectionIndex,
            question: qIndex,
        });

        const walkback = followupObj[question.key];
        if (walkback && qIndex - walkback >= 0) {
            const parentQuestion = new Question(
                questions[qIndex - walkback],
                {
                    step: stepIndex,
                    section: sectionIndex,
                    question: qIndex - walkback,
                }
            );
            map[question.key] = { parentKey: parentQuestion.key };
        }
    });

    if (Object.keys(map).length > 0)
        console.log("Computed followup map for section", sectionIndex, ":", map);

    return map;
}

/**
 * Compute a visibility map for all questions in a section
 * @param followupMap Output of computeFollowupMap
 * @param parentKeys Array of parent keys
 * @param parentValues Array of watched parent values
 * @param questions Section questions array
 * @param stepIndex Step index
 * @param sectionIndex Section index
 */
export const computeVisibilityMap = (
    followupMap: Record<string, { parentKey: string }>,
    parentKeys: string[],
    parentValues: any[],
    questions: any[],
    stepIndex: number,
    sectionIndex: number
) => {
    const map: Record<string, boolean> = {};
    function isQuestionVisible(questionKey: string): boolean {
        if (map.hasOwnProperty(questionKey)) return map[questionKey];

        const followupInfo = followupMap[questionKey];
        if (!followupInfo) {
            map[questionKey] = true;
            return true;
        }

        const parentValueIndex = parentKeys.indexOf(followupInfo.parentKey);
        const parentHasValue = parentValueIndex >= 0 && Boolean(parentValues[parentValueIndex]);
        const parentIsVisible = isQuestionVisible(followupInfo.parentKey);
        const result = parentHasValue && parentIsVisible;
        map[questionKey] = result;
        return result;
    }

    questions.forEach((qObj, qIndex) => {
        const question = new Question(qObj, {
            step: stepIndex,
            section: sectionIndex,
            question: qIndex,
        });
        isQuestionVisible(question.key);
    });

    return map;
}
