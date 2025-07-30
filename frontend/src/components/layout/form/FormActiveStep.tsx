import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import Stack from "@mui/material/Stack";
import React from "react";
import {
    useFormContext,
    type FieldValues,
    type SubmitErrorHandler
} from "react-hook-form";

import { Question, type IFormSection, type IFormStep } from "../../../context/FormTypes";
import { CheckboxInput } from "../../inputs/checkbox";
import { DateInput } from "../../inputs/date";
import { GridInput } from "../../inputs/grid";
import { NumberInput } from "../../inputs/number";
import { SelectInput } from "../../inputs/select";
import { TextInput } from "../../inputs/text";
import { TextAreaInput } from "../../inputs/textarea";


export const FormActiveStep = ({
    handleBack, handleContinue,
    currentStep, stepIndex,
}: {
    handleBack: () => void;
    handleContinue: (data: FieldValues) => void;
    currentStep: IFormStep;
    stepIndex: number;
}) => {

    // We only need submit handler here from the form context
    const { handleSubmit } = useFormContext();

    return (
        <Box className="bg-gray-300 p-8 min-w-4xl max-w-7xl">
            <form onSubmit={handleSubmit(handleContinue, onError)} onKeyDown={onKeyDown}>
                {currentStep.sections.map((section, sectionIndex) => {
                    return <Section
                        key={stepIndex + "-" + sectionIndex}
                        stepIndex={stepIndex}
                        section={section}
                        sectionIndex={sectionIndex}
                    />
                })}

                <Box justifyContent={"space-around"} display="flex" mt={4}>
                    {stepIndex !== 0 && (
                        <Button variant="outlined" onClick={handleBack}>
                            Back
                        </Button>
                    )}

                    <Button variant="contained" type="submit">
                        Continue
                    </Button>
                </Box>
            </form>
        </Box>
    );
}


// Do custom scroll and focus because ...
// MUI wraps input elements in many layers and default behaviour is buggy
const onError: SubmitErrorHandler<FieldValues> = (errors) => {
    // console.log('errors:', errors)
    const firstErrorField = Object.keys(errors)[0];

    // Try to find a container with the id
    const errorElement = document.getElementById(`feild-${firstErrorField}`) as HTMLElement;

    if (errorElement) {
        errorElement.scrollIntoView({ behavior: "smooth", block: "center" });

        // Only focus if tabIndex is not -1 
        // (skip components that are not meant to be focused)
        if (typeof errorElement.focus === "function" && errorElement.tabIndex !== -1)
            errorElement.focus();
    }
}

// Prevent default form submission on Enter key
const onKeyDown = (event: React.KeyboardEvent<HTMLFormElement>) => {
    if (event.key === "Enter") {
        event.preventDefault();
    }
}

const Section = ({
    stepIndex, section, sectionIndex,
}: {
    stepIndex: number,
    section: IFormSection,
    sectionIndex: number,
}) => {
    // Convert index to letter (A, B, C, ...)
    const idxText = String.fromCharCode(65 + sectionIndex) + ")";

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
                    // For internal tracking, form validation and label formatting
                    const question = new Question(questionObj, {
                        step: stepIndex,
                        section: sectionIndex,
                        question: qIndex,
                    })

                    let inputComponent = null;
                    switch (question.o.type) {
                        case "text":
                            inputComponent = <TextInput question={question} />;
                            break;
                        case "textarea":
                            inputComponent = <TextAreaInput question={question} />;
                            break;
                        case "number":
                            inputComponent = <NumberInput question={question} />;
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
                        default:
                            throw new Error(`Unknown question type: ${question.o.type}`);
                    }

                    return (
                        <ListItem id={`field-${question.id}`} key={qIndex} className="mb-4">
                            {inputComponent}
                        </ListItem>
                    );
                })}
            </List>
        </Stack>
    )
}