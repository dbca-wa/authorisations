import WarningIcon from '@mui/icons-material/Warning';
import Step from '@mui/material/Step';
import StepButton from '@mui/material/StepButton';
import StepContent from '@mui/material/StepContent';
import Stepper from '@mui/material/Stepper';
import Typography from '@mui/material/Typography';
import type React from 'react';
import type { IFormStep } from "../../../context/types/Questionnaire";
import { scrollToQuestion } from '../../../context/Utils';
import StepLabel from '@mui/material/StepLabel';


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

            <Step
                key="Review"
                completed={false}
                // disabled={activeStep < steps.length}
                disabled={false}
                expanded={activeStep === steps.length}
            >
                <StepItem
                    step={{ title: "Review", description: "Check your application before you submit.", sections: [] }}
                    index={steps.length}
                    activeStep={activeStep}
                    drawerOpen={drawerOpen}
                    onClick={() => handleStepClick(steps.length)}
                />
            </Step>
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


    const error: boolean = index == activeStep;
    const isDisabled = index > activeStep;
    
    const icon = error ? <WarningIcon color="error" /> : null

    // If the drawer is closed, we only show the step icon
    if (!drawerOpen) {
        // Checkmark icon if the step is in past
        return (
            <StepButton
                onClick={onClick}
                disabled={isDisabled}
                icon={icon}
            />
        );
    }

    // If the drawer is open, we show the step label and content
    return (
        <>
            <StepButton
                disabled={isDisabled}
                icon={icon}
                onClick={onClick}
            >
                <Typography fontWeight="fontWeightBold" >{step.title}</Typography>
            </StepButton>
            <StepContent>
                <Typography>{step.description}</Typography>
            </StepContent>
        </>
    );
};