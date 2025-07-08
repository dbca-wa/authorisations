import Step from '@mui/material/Step';
import StepContent from '@mui/material/StepContent';
import StepIcon from '@mui/material/StepIcon';
import StepLabel from '@mui/material/StepLabel';
import Stepper from '@mui/material/Stepper';
import Typography from '@mui/material/Typography';
import type { IFormStep } from '../../context/FormTypes';


export function ApplicationSteps({
    steps, activeStep, drawerOpen,
}: Readonly<{
    steps: IFormStep[];
    activeStep: number;
    drawerOpen: boolean;
}>) {
    return (
        <Stepper
            activeStep={activeStep}
            orientation="vertical"
            sx={{ margin: 2.5 }}
        >
            {steps.map((step, index) => (
                <Step key={step.title} expanded={activeStep === index}>
                    <StepItem
                        step={step}
                        index={index}
                        activeStep={activeStep}
                        drawerOpen={drawerOpen}
                    />
                </Step>
            ))}
        </Stepper>
    );
}


const StepItem = ({
    step, index, activeStep, drawerOpen,
}: {
    step: IFormStep;
    index: number;
    activeStep: number;
    drawerOpen: boolean;
}) => {
    // If the drawer is closed, we only show the step icon
    if (!drawerOpen) {
        // Checkmark icon if the step is in past
        const icon = index >= activeStep ? index + 1 : "✓";
        return (
            <StepIcon
                icon={icon}
                active={activeStep >= index}
            />
        );
    }

    // If the drawer is open, we show the step label and content
    return (
        <>
            <StepLabel>
                {step.title}
            </StepLabel>
            <StepContent>
                <Typography>{step.description}</Typography>
            </StepContent>
        </>
    );
};