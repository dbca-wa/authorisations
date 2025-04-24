"use client";
import Box from '@mui/material/Box';
import ApplicationSteps from '../common/steps';
import CssBaseline from '@mui/material/CssBaseline';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import Drawer from '@mui/material/Drawer';
import { makeStyles } from '@mui/styles';

const steps = [
    {
        label: 'Terms of Service',
        description: 'Read and accept the terms of service.',
    },
    {
        label: 'Scientific Review',
        description: 'Submit your project for scientific review.',
    },
    {
        label: 'Competencies & Declarations',
        description: 'Provide your competencies and declarations.',
    },
    {
        label: 'Project Details',
        description: 'Fill in the details of your project.',
    },
    {
        label: 'Replacement',
        description: 'Describe the alternatives to animal use in your project.',
    },
    {
        label: 'Reduction',
        description: 'Explain how you will reduce the number of animals used.',
    },
    {
        label: 'Refinement',
        description: 'Outline how you will refine your methods to minimize suffering.',
    },
    {
        label: 'Adverse Effects',
        description: 'Describe any potential adverse effects on animals.',
    },
    {
        label: 'References & Sources',
        description: 'References/sources used to prepare this application.',
    },
    {
        label: 'Review & Submit',
        description: 'Review your application and submit it.',
    },
];

const drawerWidth = 320;
const useStyles = makeStyles({
    drawerPaper: {
        backgroundColor: "transparent",
        marginTop: "84px",
        paddingBottom: "84px",
        paddingLeft: "30px",
    }
});


export default function FormLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    const classes = useStyles();

    // 2 column layout with steps on the left and form on the right
    return (
        <Box sx={{ display: 'flex' }}>
            {/* <CssBaseline /> */}
            <AppBar position="fixed">
                <Toolbar>
                    <Typography variant="h6" noWrap component="div">
                        Animal Ethics Committee
                    </Typography>
                </Toolbar>
            </AppBar>
            <Drawer
                classes={{ paper: classes.drawerPaper }}
                sx={{
                    width: drawerWidth,
                    flexShrink: 0,
                    '& .MuiDrawer-paper': {
                        width: drawerWidth,
                        boxSizing: 'border-box',
                    },
                }}
                variant="permanent"
                anchor="left"
            >
                <ApplicationSteps steps={steps} />

            </Drawer>
            <Box
                component="main"
                sx={{ flexGrow: 1, p: 3 }}
            >
                <Toolbar />
                {children}

            </Box>
        </Box>
    );
}