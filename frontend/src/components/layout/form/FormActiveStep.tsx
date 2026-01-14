import KeyboardArrowLeftRoundedIcon from '@mui/icons-material/KeyboardArrowLeftRounded';
import KeyboardArrowRightRoundedIcon from '@mui/icons-material/KeyboardArrowRightRounded';
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import Stack from "@mui/material/Stack";
import React from "react";

import { useWatch } from 'react-hook-form';
import type { AsyncVoidAction } from "../../../context/types/Generic";
import { Question, type IFormSection, type IFormStep } from "../../../context/types/Questionnaire";
import { CheckboxInput } from "../../inputs/checkbox";
import { DateInput } from "../../inputs/date";
import { FileInput } from "../../inputs/file";
import { GridInput } from "../../inputs/grid";
import { SelectInput } from "../../inputs/select";
import { TextInput } from "../../inputs/text";
import { computeFollowupMap } from "./visibility";


export const FormActiveStep = ({
    handleSubmit,
    applicationKey,
    currentStep,
    activeStep,
}: {
    handleSubmit: (nextStep: React.SetStateAction<number>) => AsyncVoidAction;
    applicationKey: string;
    currentStep: IFormStep;
    activeStep: number;
}) => {

    return (
        <Box className="bg-gray-300 p-8 min-w-4xl max-w-7xl">
            <form onSubmit={handleSubmit((prev) => prev + 1)} onKeyDown={onKeyDown}>
                {currentStep.sections.map((section, sectionIndex) => {
                    return <Section
                        applicationKey={applicationKey}
                        key={activeStep + "." + sectionIndex}
                        stepIndex={activeStep}
                        section={section}
                        sectionIndex={sectionIndex}
                    />
                })}

                <Box justifyContent={"space-around"} display="flex" mt={4}>
                    {activeStep !== 0 && (
                        <Button
                            variant="outlined"
                            size="large"
                            startIcon={<KeyboardArrowLeftRoundedIcon />}
                            onClick={handleSubmit((prev) => prev - 1)}
                        >
                            Back
                        </Button>
                    )}

                    <Button
                        variant="contained"
                        size="large"
                        endIcon={<KeyboardArrowRightRoundedIcon />}
                        type="submit"
                    >
                        Continue
                    </Button>
                </Box>
            </form>
        </Box>
    );
}


// Prevent default form submission on Enter key
const onKeyDown = (event: React.KeyboardEvent<HTMLFormElement>) => {
    if (event.key !== "Enter") return;

    const target = event.target as HTMLElement | null;
    if (!target) return;

    // Allow Enter when:
    //  - real <textarea>
    //  - elements marked with data-allow-enter (on the element or an ancestor)
    //  - contentEditable elements
    const tag = (target.tagName || "").toLowerCase();
    const isTextArea = tag === "textarea";
    const isContentEditable = (target as HTMLElement).isContentEditable;
    const hasAllowAttr = Boolean(target.closest && target.closest("[data-allow-enter]"));

    if (isTextArea || isContentEditable || hasAllowAttr) {
        // allow newline / default behavior
        return;
    }

    // otherwise prevent form submit
    event.preventDefault();
}

const Section = ({
    applicationKey,
    stepIndex, section, sectionIndex,
}: {
    applicationKey: string,
    stepIndex: number,
    section: IFormSection,
    sectionIndex: number,
}) => {
    // Convert index to letter (A, B, C, ...)
    const idxText = String.fromCharCode(65 + sectionIndex) + ")";
    // const { control } = useFormContext();

    // Define follow-up rules once (temporary, to be moved into data model)
    const followupObj: { [key: string]: number } = {
        "3.2-1": 1,
        "3.2-2": 1,
        "3.2-3": 2,
    };

    // Build followup map
    const followupMap = React.useMemo(
        () => computeFollowupMap(section.questions, stepIndex, sectionIndex, followupObj),
        [section.questions, stepIndex, sectionIndex]
    );

    // Helper to get a question's parent value using useWatch
    const getParentValue = (parentKey: string) => {
        // If no parent, always visible
        if (!parentKey) return true;
        // useWatch expects a field name, which is the key
        return useWatch({ name: parentKey });
    };

    // Helper to recursively check visibility for a question
    const isQuestionVisible = React.useCallback((questionKey: string): boolean => {
        const followupInfo = followupMap[questionKey];
        if (!followupInfo) return true;
        const parentValue = getParentValue(followupInfo.parentKey);
        const parentIsVisible = isQuestionVisible(followupInfo.parentKey);
        return Boolean(parentValue) && parentIsVisible;
    }, [followupMap]);

    return (
        <Stack
            component="section"
            sx={{
                backgroundColor: "white",
                width: "100%",
                boxShadow: 3,
                borderRadius: 2,
                p: 4,
                mb: 6,
            }}
        >
            <h2 className="text-2xl font-bold mb-4">
                {idxText} {section.title}
            </h2>
            {section.description &&
                <p className="mb-6 display-linebreak">
                    {section.description}
                </p>
            }

            <List>
                {section.questions.map((questionObj, qIndex) => {
                    const question = new Question(questionObj, {
                        step: stepIndex,
                        section: sectionIndex,
                        question: qIndex,
                    });

                    // Check visibility using useWatch and recursive logic
                    if (!isQuestionVisible(question.key)) {
                        return null;
                    }

                    let inputComponent = null;
                    switch (question.o.type) {
                        case "text":
                        case "textarea":
                        case "number":
                            inputComponent = <TextInput question={question} />;
                            break;
                        case "checkbox":
                            inputComponent = <CheckboxInput question={question} />;
                            break;
                        case "select":
                            inputComponent = <SelectInput question={question} />;
                            break;
                        case "date":
                            inputComponent = <DateInput question={question} />;
                            break;
                        case "grid":
                            inputComponent = <GridInput question={question} />;
                            break;
                        case "file":
                            inputComponent = <FileInput question={question} applicationKey={applicationKey} />;
                            break;
                        default:
                            throw new Error(`Unknown question type: ${question.o.type}`);
                    }

                    return (
                        <ListItem id={`q-${question.key}`} key={qIndex} className="mb-4">
                            {inputComponent}
                        </ListItem>
                    );
                })}
            </List>
        </Stack>
    )
}