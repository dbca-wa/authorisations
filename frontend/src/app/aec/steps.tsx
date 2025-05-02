import Box from '@mui/material/Box';
import Stepper from '@mui/material/Stepper';
import Step from '@mui/material/Step';
import StepLabel from '@mui/material/StepLabel';
import StepContent from '@mui/material/StepContent';
import Button from '@mui/material/Button';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import { Section } from '@/app/data/FormData';


export default function ApplicationSteps({
    sections, activeSection,
}: Readonly<{
    sections: Section[];
    activeSection: number;
}>) {
    return (
        <Box sx={{ maxWidth: 400 }}>
            <Stepper activeStep={activeSection} orientation="vertical">
                {sections.map((section, index) => (
                    <Step key={section.title} expanded={activeSection === index}>
                        <StepLabel>
                            {section.title}
                        </StepLabel>
                        <StepContent>
                            <Typography>{section.shortDescription}</Typography>
                        </StepContent>
                    </Step>
                ))}
            </Stepper>
            {activeSection === sections.length && (
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