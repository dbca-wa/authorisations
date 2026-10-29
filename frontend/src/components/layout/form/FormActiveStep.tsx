import KeyboardArrowLeftRoundedIcon from '@mui/icons-material/KeyboardArrowLeftRounded';
import KeyboardArrowRightRoundedIcon from '@mui/icons-material/KeyboardArrowRightRounded';
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Collapse from "@mui/material/Collapse";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import Stack from "@mui/material/Stack";
import React from "react";

import { useWatch, type ControllerRenderProps, type FieldValues } from 'react-hook-form';
import { computeDependentQuestionMap, computeDependentQuestionVisibilityMap } from '../../../context/DependentQuestions';
import type { IApplicationAttachment } from '../../../context/types/Application';
import type { AsyncVoidAction } from "../../../context/types/Generic";
import { Question, type IFormSection, type IFormStep } from "../../../context/types/Questionnaire";
import { CheckboxInput } from "../../inputs/checkbox";
import { DateInput } from "../../inputs/date";
import { FileInput } from "../../inputs/file";
import { GridInput } from "../../inputs/grid";
import { SelectInput } from "../../inputs/select";
import { TextInput } from "../../inputs/text";


export const FormActiveStep = ({
    handleSubmit,
    onAttachmentAdded,
    onAttachmentDeleted,
    onAttachmentUpdated,
    applicationKey,
    currentStep,
    attachments,
    activeStep,
}: {
    handleSubmit: (nextStep: React.SetStateAction<number>) => AsyncVoidAction;
    onAttachmentAdded: (newAttachment: IApplicationAttachment, field: ControllerRenderProps<FieldValues, string>) => void;
    onAttachmentDeleted: (attachmentKey: string, field: ControllerRenderProps<FieldValues, string>) => void;
    onAttachmentUpdated: (updatedAttachment: IApplicationAttachment) => void;
    applicationKey: string;
    currentStep: IFormStep;
    attachments: IApplicationAttachment[];
    activeStep: number;
}) => {

    return (
        <Box className="bg-gray-300 p-8 w-full min-w-3xl lg:w-3xl xl:w-4xl 2xl:w-6xl">
            <form onSubmit={handleSubmit((prev) => prev + 1)} onKeyDown={onKeyDown}>
                {currentStep.sections.map((section, sectionIndex) => {
                    return <Section
                        key={activeStep + "." + sectionIndex}
                        applicationKey={applicationKey}
                        stepIndex={activeStep}
                        section={section}
                        sectionIndex={sectionIndex}
                        attachments={attachments}
                        onAttachmentAdded={onAttachmentAdded}
                        onAttachmentDeleted={onAttachmentDeleted}
                        onAttachmentUpdated={onAttachmentUpdated}
                    />
                })}

                <Box sx={{ justifyContent: "space-around", display: "flex", mt: 4 }}>
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

/**
 * The component that groups questions and responsible for handling 
 * the dependent question visibility logic.
 */
const Section = ({
    applicationKey,
    stepIndex, section, sectionIndex,
    attachments,
    onAttachmentAdded,
    onAttachmentDeleted,
    onAttachmentUpdated,
}: {
    applicationKey: string,
    stepIndex: number,
    section: IFormSection,
    sectionIndex: number,
    attachments: IApplicationAttachment[];
    onAttachmentAdded: (newAttachment: IApplicationAttachment, field: ControllerRenderProps<FieldValues, string>) => void;
    onAttachmentDeleted: (attachmentKey: string, field: ControllerRenderProps<FieldValues, string>) => void;
    onAttachmentUpdated: (updatedAttachment: IApplicationAttachment) => void;
}) => {
    // Convert section index to letter (A, B, C, ...)
    const idxText = String.fromCharCode(65 + sectionIndex) + ")";

    // Build dependent question map
    const dependentQuestionMap = React.useMemo(
        () => computeDependentQuestionMap(section.questions, stepIndex, sectionIndex),
        [section.questions, stepIndex, sectionIndex]
    );

    // collect unique parent keys in a stable order
    const parentKeys: readonly string[] = React.useMemo(
        () => Array.from(new Set(Object.values(dependentQuestionMap).map(v => v.parentKey).filter(Boolean))).sort(),
        [dependentQuestionMap]
    );

    // single useWatch call (top-level) for all parents
    const parentValuesArray = useWatch({ name: parentKeys });

    // map array -> keyed object
    const parentValues = React.useMemo(() => {
        const m: Record<string, unknown> = {};
        if (Array.isArray(parentValuesArray)) {
            parentKeys.forEach((k, i) => { m[k] = parentValuesArray?.[i]; });
        } else if (parentValuesArray && typeof parentValuesArray === 'object') {
            parentKeys.forEach((k) => { m[k] = (parentValuesArray as Record<string, unknown>)[k]; });
        }
        return m;
    }, [parentKeys, parentValuesArray]);

    // compute visibility once per render
    const visibilityMap = React.useMemo(() => {
        return computeDependentQuestionVisibilityMap({
            dependentQuestionMap,
            answerValuesByQuestionKey: parentValues,
        });
    }, [dependentQuestionMap, parentValues]);

    // small wrapper used by render code
    const isQuestionVisible = React.useCallback((questionKey: string): boolean => {
        return visibilityMap[questionKey] ?? true;
    }, [visibilityMap]);

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

                    // Determine visibility for this question using cached visibility map
                    const isVisible = isQuestionVisible(question.key);

                    let inputComponent: React.ReactNode;
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
                        case "file":
                            inputComponent = <FileInput question={question}
                                applicationKey={applicationKey}
                                attachments={attachments.filter(atch => atch.question === question.key)}
                                onAttachmentAdded={onAttachmentAdded}
                                onAttachmentDeleted={onAttachmentDeleted}
                                onAttachmentUpdated={onAttachmentUpdated}
                            />;
                            break;
                        case "grid":
                            inputComponent = <GridInput question={question} />;
                            break;
                        default:
                            throw new Error(`Unknown question type: ${question.o.type}`);
                    }

                    // Wrap in Collapse for smooth slide down/up animation of dependent questions.
                    // timeout="auto" calculates duration based on content height for natural feel.
                    return (
                        <Collapse in={isVisible} timeout="auto" key={qIndex}>
                            <ListItem id={`q-${question.key}`} className="mb-4 w-full">
                                {isVisible && inputComponent}
                            </ListItem>
                        </Collapse>
                    );
                })}
            </List>
        </Stack>
    )
}
