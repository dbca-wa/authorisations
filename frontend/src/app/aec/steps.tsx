import Box from '@mui/material/Box';
import Stepper from '@mui/material/Stepper';
import Step from '@mui/material/Step';
import StepLabel from '@mui/material/StepLabel';
import StepContent from '@mui/material/StepContent';
import Button from '@mui/material/Button';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import { FormStep } from '@/app/data/FormData';


export function ApplicationSteps({
    steps, activeStep,
}: Readonly<{
    steps: FormStep[];
    activeStep: number;
}>) {
    return (
        <Box sx={{ maxWidth: 400 }}>
            <Stepper activeStep={activeStep} orientation="vertical">
                {steps.map((step, index) => (
                    <Step key={step.title} expanded={activeStep === index}>
                        <StepLabel>
                            {step.title}
                        </StepLabel>
                        <StepContent>
                            <Typography>{step.shortDescription}</Typography>
                        </StepContent>
                    </Step>
                ))}
            </Stepper>
            {activeStep === steps.length && (
                <Paper square elevation={0} sx={{ p: 3 }}>
                    <Typography>All steps completed - you&apos;re finished</Typography>
                    <Button
                        // onClick={handleReset}
                        sx={{ mt: 1, mr: 1 }}
                    >
                        Reset
                    </Button>
                </Paper>
            )}
        </Box>
    );
}