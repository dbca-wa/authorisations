import Drawer from '@mui/material/Drawer';
import type { FormStep } from '../../context/FormTypes';
import { ApplicationSteps } from './ApplicationSteps';


const drawerWidth = 320;

export function Sidebar({
    steps,
    activeStep
}: Readonly<{
    steps: FormStep[],
    activeStep: number,
}>) {
    return (
        <Drawer
            sx={{
                width: drawerWidth,
                flexShrink: 0,
                '& .MuiDrawer-paper': {
                    width: drawerWidth,
                    boxSizing: 'border-box',
                    backgroundColor: "transparent",
                    marginTop: "84px",
                    paddingBottom: "84px",
                    paddingLeft: "30px",
                },
            }}
            variant="permanent"
            anchor="left"
        >
            <ApplicationSteps
                steps={steps}
                activeStep={activeStep}
            />
        </Drawer>
    );
}