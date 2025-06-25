"use client";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import React from "react";
import { FormStepContext } from "../../context/FormContext";
import { CheckboxInput } from "../inputs/checkbox";
import { DateInput } from "../inputs/date";
import { GridInput } from "../inputs/grid";
import { NumberInput } from "../inputs/number";
import { SelectInput } from "../inputs/select";
import { TextInput } from "../inputs/text";
import { TextAreaInput } from "../inputs/textarea";


export function ActiveStepForm() {
    // Destructure values from the context
    const {
        setActiveStep, currentStep,
        isFirst, isLast,
    } = React.useContext(FormStepContext);
    // const step = formData.steps[activeSection];

    const handleBack = () => {
        setActiveStep((prevStep) => prevStep - 1); // Update the step
    };

    const handleNext = () => {
        setActiveStep((prevStep) => prevStep + 1); // Update the step
    };

    // Show dummy confirmation message for now
    const handleSubmit = () => {
        alert("Form submitted successfully! - NOT");
    }

    return (
        <div className="bg-gray-300 p-8 min-w-3xl max-w-7xl">
            <form>
                {currentStep.sections.map((section, sIndex) => {
                    // Convert index to letter (A, B, C, ...)
                    const idxText = String.fromCharCode(65 + sIndex) + ")";

                    return (
                        <section key={section.title} className="bg-white w-full shadow-lg rounded-lg p-8 mb-6">
                            <h2 className="text-2xl font-bold mb-4">
                                {idxText} {section.title}
                            </h2>
                            <p className="mb-6 display-linebreak">
                                {section.description}
                            </p>

                            <List>
                                {section.questions.map((question, qIndex) => {
                                    // Assign index to question for display purposes only
                                    // Do not display if there is only one question in the section
                                    question.indexText = section.questions.length > 1
                                        ? `${qIndex + 1}. ` : "";

                                    if (question.type === "text") {
                                        return (
                                            <ListItem key={qIndex} className="mb-2">
                                                <TextInput question={question} />
                                            </ListItem>
                                        )
                                    }
                                    else if (question.type === "textarea") {
                                        return (
                                            <ListItem key={qIndex} className="mb-6">
                                                <TextAreaInput question={question} />
                                            </ListItem>
                                        )
                                    }
                                    else if (question.type === "number") {
                                        return (
                                            <ListItem key={qIndex} className="mb-6">
                                                <NumberInput question={question} />
                                            </ListItem>
                                        )
                                    }
                                    else if (question.type === "checkbox") {
                                        return (
                                            <ListItem key={qIndex} className="mb-1">
                                                <CheckboxInput question={question} />
                                            </ListItem>
                                        )
                                    }
                                    else if (question.type === "select") {
                                        return (
                                            <ListItem key={qIndex} className="mb-6">
                                                <SelectInput question={question} />
                                            </ListItem>
                                        )
                                    }
                                    else if (question.type === "date") {
                                        return (
                                            <ListItem key={qIndex} className="mb-4">
                                                <DateInput question={question} />
                                            </ListItem>
                                        )
                                    }
                                    else if (question.type === "grid") {
                                        return (
                                            <ListItem key={qIndex} className="mb-8">
                                                <GridInput {...question} />
                                            </ListItem>
                                        )
                                    }
                                })}

                            </List>

                        </section>
                    )
                })}

                <Box justifyContent={"space-around"} display="flex" mt={4}>
                    {!isFirst && (
                        <Button variant="outlined" onClick={handleBack} className="mr-4">
                            Back
                        </Button>
                    )}

                    {!isLast && (
                        <Button variant="contained" onClick={handleNext}>
                            Continue
                        </Button>
                    )}

                    {isLast && (
                        <Button variant="contained" onClick={handleSubmit}>
                            Submit
                        </Button>
                    )}
                </Box>
            </form>
        </div>
    );
}
