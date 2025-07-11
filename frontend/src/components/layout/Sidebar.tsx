import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import Divider from '@mui/material/Divider';
import MuiDrawer from '@mui/material/Drawer';
import IconButton from '@mui/material/IconButton';
import { styled, type CSSObject, type Theme } from '@mui/material/styles';
import type { IFormStep } from '../../context/FormTypes';
import { ApplicationSteps } from './ApplicationSteps';
import { DRAWER_WIDTH } from '../../context/Constants';


export function Sidebar({
    steps,
    activeStep,
    drawerOpen,
    setDrawerOpen,
}: Readonly<{
    steps: IFormStep[];
    activeStep: number;
    drawerOpen: boolean;
    setDrawerOpen: (open: boolean) => void;
}>) {
    return (
        <Drawer
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
            <ApplicationSteps
                steps={steps}
                activeStep={activeStep}
                drawerOpen={drawerOpen}
            />
        </Drawer>
    );
}


const Drawer = styled(MuiDrawer, { shouldForwardProp: (prop) => prop !== 'open' })(
    ({ theme }) => ({
        width: DRAWER_WIDTH,
        flexShrink: 0,
        boxSizing: 'border-box',
        variants: [
            {
                props: ({ open }) => open,
                style: {
                    ...openedMixin(theme),
                    '& .MuiDrawer-paper': openedMixin(theme),
                },
            },
            {
                props: ({ open }) => !open,
                style: {
                    ...closedMixin(theme),
                    '& .MuiDrawer-paper': closedMixin(theme),
                },
            },
        ],
    }),
);

const DrawerHeader = styled('div')(({ theme }) => ({
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'flex-end',
    padding: theme.spacing(0, 1),
    // necessary for content to be below app bar
    ...theme.mixins.toolbar,
}));

const openedMixin = (theme: Theme): CSSObject => ({
    width: DRAWER_WIDTH,
    transition: theme.transitions.create('width', {
        easing: theme.transitions.easing.sharp,
        duration: theme.transitions.duration.enteringScreen,
    }),
    overflowX: 'hidden',
});

const closedMixin = (theme: Theme): CSSObject => ({
    transition: theme.transitions.create('width', {
        easing: theme.transitions.easing.sharp,
        duration: theme.transitions.duration.leavingScreen,
    }),
    overflowX: 'hidden',
    width: `calc(${theme.spacing(7)} + 1px)`,
    [theme.breakpoints.up('sm')]: {
        width: `calc(${theme.spacing(8)} + 1px)`,
    },
});
