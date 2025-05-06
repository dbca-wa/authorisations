"use client";
import { FormStepContext } from "@/app/context/FormContext";
import { GridQuestion } from "@/app/data/FormData";
import { CheckboxInput } from "@/app/inputs/checkbox";
import { GridInput } from "@/app/inputs/grid";
import { MultiSelectInput } from "@/app/inputs/multiselect";
import { TextInput } from "@/app/inputs/text";
import { Box, List, ListItem } from "@mui/material";
import Button from "@mui/material/Button";
import React from "react";
import { TextAreaInput } from "../inputs/textarea";
import { DateInput } from "../inputs/date";


export default function Page() {
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
        <div className="mt-4 bg-gray-300 p-8 rounded-lg shadow-lg w-full max-w-5xl">
            <form>
                {currentStep.sections.map((section, _) => {
                    return (
                        <section key={section.title} className="bg-white shadow-lg rounded-lg p-8 mb-6">
                            <h2 className="text-2xl font-bold mb-4">
                                {section.title}
                            </h2>
                            <p className="mb-6 display-linebreak">
                                {section.description}
                            </p>

                            <List>
                                {section.questions.map((question, index) => {
                                    if (question.type === "text") {
                                        return (
                                            <ListItem key={index}>
                                                <TextInput question={question} />
                                            </ListItem>
                                        )
                                    }
                                    if (question.type === "textarea") {
                                        return (
                                            <ListItem key={index}>
                                                <TextAreaInput question={question} />
                                            </ListItem>
                                        )
                                    }
                                    else if (question.type === "checkbox") {
                                        return (
                                            <ListItem key={index}>
                                                <CheckboxInput question={question} />
                                            </ListItem>
                                        )
                                    }
                                    else if (question.type === "multiselect") {
                                        return (
                                            <ListItem key={index}>
                                                <MultiSelectInput question={question} />
                                            </ListItem>
                                        )
                                    }
                                    else if (question.type === "date") {
                                        return (
                                            <ListItem key={index}>
                                                <DateInput question={question} />
                                            </ListItem>
                                        )
                                    }
                                    else if (question.type === "grid") {
                                        return (
                                            <ListItem key={index}>
                                                <GridInput {...question as GridQuestion} />
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
