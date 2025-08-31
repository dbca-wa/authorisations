import Step from '@mui/material/Step';
import StepButton from '@mui/material/StepButton';
import StepContent from '@mui/material/StepContent';
import Stepper from '@mui/material/Stepper';
import Typography from '@mui/material/Typography';
import type React from 'react';
import type { IFormStep } from "../../../context/types/Questionnaire";
import { scrollToQuestion } from '../../../context/Utils';


export function FormSteps({
    steps, activeStep, saveAnswers, setActiveStep, drawerOpen,
}: Readonly<{
    steps: IFormStep[];
    activeStep: number;
    saveAnswers: () => Promise<void>;
    setActiveStep: React.Dispatch<React.SetStateAction<number>>;
    drawerOpen: boolean;
}>) {
    const handleStepClick = async (index: number) => {
        // Allow clicking the current step to scroll to top of it
        if (index === activeStep) {
            scrollToQuestion({ stepIndex: index });
        }
        // Allow clicking previous (completed) steps to navigate back
        else if (index < activeStep) {
            await saveAnswers();
            setActiveStep(index);
        }
        // Clicks on future steps are disabled and will do nothing.
    };

    return (
        <Stepper
            activeStep={activeStep}
            orientation="vertical"
            sx={{ margin: 2.5 }}
        >
            {steps.map((step, index) => (
                <Step
                    key={step.title}
                    completed={index < activeStep}
                    disabled={index > activeStep}
                    expanded={activeStep === index}
                >
                    <StepItem
                        step={step}
                        index={index}
                        activeStep={activeStep}
                        drawerOpen={drawerOpen}
                        onClick={() => handleStepClick(index)}
                    />
                </Step>
            ))}
        </Stepper>
    );
}


const StepItem = ({
    step, index, activeStep,
    drawerOpen, onClick,
}: {
    step: IFormStep;
    index: number;
    activeStep: number;
    drawerOpen: boolean;
    onClick: () => void;
}) => {
    const isDisabled = index > activeStep;

    // If the drawer is closed, we only show the step icon
    if (!drawerOpen) {
        // Checkmark icon if the step is in past
        // const icon = index >= activeStep ? index + 1 : "✓";
        return (
            <StepButton onClick={onClick} disabled={isDisabled} />
        );
    }

    // If the drawer is open, we show the step label and content
    return (
        <>
            <StepButton onClick={onClick} disabled={isDisabled}>
                {step.title}
            </StepButton>
            {activeStep === index &&
                <StepContent>
                    <Typography>{step.description}</Typography>
                </StepContent>
            }
        </>
    );
};