import WarningIcon from '@mui/icons-material/Warning';
import Step from '@mui/material/Step';
import StepButton from '@mui/material/StepButton';
import StepContent from '@mui/material/StepContent';
import Stepper from '@mui/material/Stepper';
import Typography from '@mui/material/Typography';
import type React from 'react';
import type { AsyncVoidAction, NumberedBooleanObj } from '../../../context/types/Generic';
import type { IFormStep } from "../../../context/types/Questionnaire";


const reviewStep = {
    title: "Review",
    description: "Check your application before you submit.",
    sections: [],
};

export function FormSteps({
    drawerOpen,
    steps, activeStep,
    handleSubmit,
    validatedSteps,
}: Readonly<{
    drawerOpen: boolean;
    steps: IFormStep[];
    activeStep: number;
    handleSubmit: (nextStep: React.SetStateAction<number>) => AsyncVoidAction;
    validatedSteps: NumberedBooleanObj;
}>) {
    const handleStepClick = async (index: number) => {
        // Current step
        if (index === activeStep) {
            // Do nothing 
            // scrollToQuestion({ stepIndex: index });
        }
        // Previous or future steps that we can click
        else {
            await handleSubmit(index)();
        }
    };

    return (
        <Stepper
            activeStep={activeStep}
            orientation="vertical"
            sx={{ margin: 2.5 }}
        >
            {steps.map((step, index) => {
                const isCompleted: boolean = validatedSteps[index] || false;
                const hasError: boolean = validatedSteps[index] === false;

                return <Step
                    key={index}
                    completed={isCompleted}
                    disabled={!isCompleted}
                    expanded={activeStep === index}
                >
                    <StepItem
                        step={step}
                        drawerOpen={drawerOpen}
                        onClick={() => handleStepClick(index)}
                        isActive={activeStep === index}
                        hasError={hasError}
                    />
                </Step>
            })}

            <Step
                key={steps.length}
                completed={false}
                disabled={true}
                expanded={activeStep === steps.length}
            >
                <StepItem
                    step={reviewStep}
                    drawerOpen={drawerOpen}
                    onClick={() => handleStepClick(steps.length)}
                    isActive={activeStep === steps.length}
                    hasError={false}
                />
            </Step>
        </Stepper>
    );
}


const StepItem = ({
    step,
    drawerOpen,
    onClick,
    isActive,
    hasError,
}: {
    step: IFormStep;
    drawerOpen: boolean;
    onClick: () => void;
    isActive: boolean;
    hasError: boolean;
}) => {
    const icon = hasError ? <WarningIcon color="error" /> : null;

    // If the drawer is closed, we only show the step icon
    if (!drawerOpen) {
        // Checkmark icon if the step is in past
        return (
            <StepButton icon={icon} onClick={onClick} />
        );
    }

    // If the drawer is open, we show the step label and content
    return (
        <>
            <StepButton icon={icon} onClick={onClick}>
                <Typography fontWeight={isActive ? "fontWeightBold" : "fontWeightRegular"}>
                    {step.title}
                </Typography>
            </StepButton>
            <StepContent>
                <Typography>{step.description}</Typography>
            </StepContent>
        </>
    );
};