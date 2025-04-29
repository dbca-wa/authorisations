"use client";
import React from "react";
import Button from "@mui/material/Button";
import ApplicationFormContext from "../context/FormContext";
import CheckboxInput from "@/app/inputs/checkbox";
import TextInput from "@/app/inputs/text";
import { Box, ButtonGroup, List, ListItem, ListItemText } from "@mui/material";


export default function Page() {
    // Destructure values from the context
    const { activeSection, setActiveSection, formData } = React.useContext(ApplicationFormContext);
    const section = formData.sections[activeSection];
    console.log("Active section in Page:", { activeSection });

    const handleNext = () => {
        console.log("Current step:", activeSection);
        setActiveSection((prevStep) => prevStep + 1); // Update the step
    };

    const handleBack = () => {
        setActiveSection((prevStep) => prevStep - 1); // Update the step
    };

    return (
        <div className="mt-4 bg-gray-300 p-8 rounded-lg shadow-lg w-full max-w-5xl">
            <form className="mx-auto p-8 bg-white shadow-lg rounded-lg">
                <h2 className="text-2xl font-bold mb-4 text-center">
                    {section.title}
                </h2>
                <p className="mb-6 display-linebreak">
                    {section.longDescription}
                </p>

                <List>
                    {section.questions.map((question, index) => {
                        if (question.type === "checkbox") {
                            return (
                                <ListItem key={index}>
                                    <CheckboxInput
                                        key={index}
                                        label={question.label}
                                        isRequired={question.isRequired}
                                    />
                                </ListItem>
                            )
                        }
                        else if (question.type === "text") {
                            return (
                                <ListItem key={index}>
                                    <TextInput
                                        key={index}
                                        label={question.label}
                                        isRequired={question.isRequired}
                                    />
                                </ListItem>
                            )
                        }

                    })}

                </List>


                <Box justifyContent={"space-around"} display="flex"  mt={4}>
                    {activeSection !== 0 && (
                        <Button variant="outlined" onClick={handleBack} className="mr-4">
                            Back
                        </Button>
                    )}

                    {activeSection !== formData.sections.length - 1 && (
                        <Button variant="contained" onClick={handleNext}>
                            Continue
                        </Button>
                    )}
                </Box>
            </form>
        </div>
    );
}
