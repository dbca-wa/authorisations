import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import Stack from "@mui/material/Stack";
import React from "react";

import type { AsyncVoidAction } from "../../../context/types/Generic";
import { Question, type IFormSection, type IFormStep } from "../../../context/types/Questionnaire";
import { CheckboxInput } from "../../inputs/checkbox";
import { DateInput } from "../../inputs/date";
import { GridInput } from "../../inputs/grid";
import { SelectInput } from "../../inputs/select";
import { TextInput } from "../../inputs/text";


export const FormActiveStep = ({
    handleSubmit,
    currentStep, 
    activeStep,
}: {
    handleSubmit: (nextStep: React.SetStateAction<number>) => AsyncVoidAction;
    currentStep: IFormStep;
    activeStep: number;
}) => {

    return (
        <Box className="bg-gray-300 p-8 min-w-4xl max-w-7xl">
            <form onSubmit={handleSubmit((prev) => prev + 1)} onKeyDown={onKeyDown}>
                {currentStep.sections.map((section, sectionIndex) => {
                    return <Section
                        key={activeStep + "." + sectionIndex}
                        stepIndex={activeStep}
                        section={section}
                        sectionIndex={sectionIndex}
                    />
                })}

                <Box justifyContent={"space-around"} display="flex" mt={4}>
                    {activeStep !== 0 && (
                        <Button variant="outlined" onClick={handleSubmit((prev) => prev - 1)}>
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