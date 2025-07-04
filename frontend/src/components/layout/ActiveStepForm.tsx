import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import React from "react";
import {
    useFormContext,
    type FieldValues,
    type SubmitHandler
} from "react-hook-form";
import { FormStepContext } from "../../context/FormContext";
import { Question, type IFormSection } from "../../context/FormTypes";
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
        setActiveStep,
        currentStep,
        stepIndex,
        isFirst, isLast,
    } = React.useContext(FormStepContext);

    // We only need submit handler here from the form context
    const { handleSubmit } = useFormContext();

    const handleBack = () => {
        setActiveStep((prevStep) => prevStep - 1); // Update the step
    };

    // const handleNext = (event: React.FormEvent<HTMLFormElement>) => {
    //     // Do not actually submit the form
    //     event.preventDefault();

    //     setActiveStep((prevStep) => prevStep + 1); // Update the step
    // };

    // Show dummy confirmation message for now
    // const handleSubmit = () => {
    //     alert("Form submitted successfully! - NOT");
    // }

    const onSubmit: SubmitHandler<FieldValues> = (data) => {
        // TODO: Do send the answers and progress to backend
        console.log("Data:", data)

        // Next step
        setActiveStep((prevStep) => prevStep + 1);
    }

    // Do custom scroll and focus because MUI wraps input elements in many layers
    const onError: SubmitHandler<FieldValues> = (errors) => {
        const firstErrorField = Object.keys(errors)[0];
        const errorElement = document.querySelector(`[name="${firstErrorField}"]`) as HTMLElement;
        if (errorElement) {
            errorElement.scrollIntoView({ behavior: "smooth", block: "center" });

            // Only focus if tabIndex is not -1 
            // (skip components that are not meant to be focused)
            if (errorElement.tabIndex !== -1)
                errorElement.focus();
        }
    }

    return (
        <div className="bg-gray-300 p-8 min-w-3xl max-w-7xl">
            <form onSubmit={handleSubmit(onSubmit, onError)}>
                {currentStep.sections.map((section, sIndex) => {
                    return <Section
                        key={stepIndex + "-" + sIndex}
                        stepIndex={stepIndex}
                        section={section}
                        sectionIndex={sIndex}
                    />
                })}

                <Box justifyContent={"space-around"} display="flex" mt={4}>
                    {!isFirst && (
                        <Button variant="outlined" onClick={handleBack}>
                            Back
                        </Button>
                    )}

                    {!isLast && (
                        <Button variant="contained" type="submit">
                            Continue
                        </Button>
                    )}

                    {isLast && (
                        <Button variant="contained" type="submit">
                            Submit
                        </Button>
                    )}
                </Box>
            </form>
        </div>
    );
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
        <section className="bg-white w-full shadow-lg rounded-lg p-8 mb-6">
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
                    let marginClass = "mb-4";
                    switch (question.o.type) {
                        case "text":
                            inputComponent = <TextInput question={question} />;
                            // marginClass = "mb-2";
                            break;
                        case "textarea":
                            inputComponent = <TextAreaInput question={question} />;
                            // marginClass = "mb-6";
                            break;
                        case "number":
                            inputComponent = <NumberInput question={question} />;
                            // marginClass = "mb-6";
                            break;
                        case "checkbox":
                            inputComponent = <CheckboxInput question={question} />;
                            // marginClass = "mb-1";
                            break;
                        case "select":
                            inputComponent = <SelectInput question={question} />;
                            // marginClass = "mb-6";
                            break;
                        case "date":
                            inputComponent = <DateInput question={question} />;
                            // marginClass = "mb-4";
                            break;
                        case "grid":
                            inputComponent = <GridInput question={question} />;
                            // marginClass = "mb-8";
                            break;
                        default:
                            throw new Error(`Unknown question type: ${question.o.type}`);
                    }

                    return (
                        <ListItem key={qIndex} className={marginClass}>
                            {inputComponent}
                        </ListItem>
                    );
                })}
            </List>
        </section>
    )
}