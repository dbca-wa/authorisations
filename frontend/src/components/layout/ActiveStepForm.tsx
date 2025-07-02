import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import React from "react";
import {
    FormProvider,
    useForm,
    type FieldValues,
    type SubmitHandler
} from "react-hook-form";
import { FormStepContext } from "../../context/FormContext";
import { CheckboxInput } from "../inputs/checkbox";
import { DateInput } from "../inputs/date";
import { GridInput } from "../inputs/grid";
import { NumberInput } from "../inputs/number";
import { SelectInput } from "../inputs/select";
import { TextInput } from "../inputs/text";
import { TextAreaInput } from "../inputs/textarea";
import { Question, type FormSection } from "../../context/FormTypes";


// type Inputs = {
//     example: string
//     exampleRequired: string
// }

export function ActiveStepForm() {
    // Destructure values from the context
    const {
        setActiveStep, currentStep, stepIndex,
        isFirst, isLast,
    } = React.useContext(FormStepContext);
    // const step = formData.steps[activeSection];

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

    const methods = useForm()
    const onSubmit: SubmitHandler<FieldValues> = (data) => console.log(data)
    // const onError: SubmitHandler<FieldValues> = (errors) => console.log(errors)

    // console.log(watch("example")) // watch input value by passing the name of it

    return (
        <div className="bg-gray-300 p-8 min-w-3xl max-w-7xl">
            <FormProvider {...methods}>
                <form onSubmit={methods.handleSubmit(onSubmit)}>
                    {currentStep.sections.map((section, sIndex) => {
                        // return <p key={sIndex}>asdasdsad</p>
                        return <Section key={sIndex} stepIndex={stepIndex} section={section} sIndex={sIndex} />
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
            </FormProvider>
        </div>
    );
}


const Section = ({
    stepIndex, section, sIndex,
}: {
    stepIndex: number,
    section: FormSection,
    sIndex: number,
}) => {
    // Convert index to letter (A, B, C, ...)
    const idxText = String.fromCharCode(65 + sIndex) + ")";

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
                        section: sIndex,
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