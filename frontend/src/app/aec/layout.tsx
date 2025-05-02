"use client";
import React from 'react';
import Box from '@mui/material/Box';
import ApplicationSteps from './steps';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import Drawer from '@mui/material/Drawer';
import makeStyles from '@mui/styles/makeStyles';
import formData from '@/app/data/formData.json';
import ApplicationFormContext from '../context/FormContext';

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
    // Manage activeStep state here
    const [activeSection, setActiveSection] = React.useState(0);
    const classes = useStyles();

    // Set the ApplicationFormContext value
    const contextValue = { activeSection, setActiveSection, formData };

    return (
        <Box sx={{ display: 'flex' }}>
            <AppBar position="fixed">
                <Toolbar>
                    <Typography variant="h6" noWrap component="div">
                        {formData.name}
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
                <ApplicationSteps
                    sections={formData.sections}
                    activeSection={activeSection}
                />
            </Drawer>
            <Box
                component="main"
                sx={{ flexGrow: 1, p: 1 }}
            >
                <Toolbar />
                <ApplicationFormContext.Provider value={contextValue}>
                    {children}
                </ApplicationFormContext.Provider>
            </Box>
        </Box>
    );
}