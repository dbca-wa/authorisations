import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import Divider from '@mui/material/Divider';
import IconButton from '@mui/material/IconButton';

import { styled } from '@mui/material/styles';
import type { AsyncVoidAction, NumberedBooleanObj } from '../../../context/types/Generic';
import type { IFormStep } from "../../../context/types/Questionnaire";
import { ResponsiveMiniDrawer } from '../StyledDrawer';
import { FormSteps } from './FormSteps';


export function FormSidebar({
    userCanEdit,
    drawerOpen,
    setDrawerOpen,
    steps,
    activeStep,
    handleSubmit,
    validatedSteps,
}: Readonly<{
    userCanEdit: boolean;
    drawerOpen: boolean;
    setDrawerOpen: (open: boolean) => void;
    steps: IFormStep[];
    activeStep: number;
    handleSubmit: (nextStep: React.SetStateAction<number>) => AsyncVoidAction;
    validatedSteps: NumberedBooleanObj;
}>) {
    return (
        <ResponsiveMiniDrawer
            sx={{
                '& .MuiDrawer-paper': {
                    backgroundColor: "transparent",
                    // border: '2px solid red',
                },
            }}
            variant="permanent"
            open={drawerOpen}
        >
            <DrawerHeader>
                <IconButton
                    aria-label="close drawer"
                    onClick={() => setDrawerOpen(!drawerOpen)}
                >
                    <ChevronLeftIcon />
                </IconButton>
            </DrawerHeader>
            <Divider />
            <FormSteps
                userCanEdit={userCanEdit}
                drawerOpen={drawerOpen}
                steps={steps}
                activeStep={activeStep}
                handleSubmit={handleSubmit}
                validatedSteps={validatedSteps}
            />
        </ResponsiveMiniDrawer>
    );
}

const DrawerHeader = styled('div')(({ theme }) => ({
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'flex-end',
    padding: theme.spacing(0, 1),
    // necessary for content to be below app bar
    ...theme.mixins.toolbar,
}));
