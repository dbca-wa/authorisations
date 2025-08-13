import AppBar from '@mui/material/AppBar';
import Box from '@mui/material/Box';
import CssBaseline from '@mui/material/CssBaseline';
import Drawer from '@mui/material/Drawer';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';

import { DRAWER_WIDTH } from '../../../context/Constants';
import type { IRoute } from "../../../context/types/Generic";
import { ROUTES } from '../../../router';


export const MainLayout = ({
    route,
}: {
    route: IRoute,
}) => {
    return (
        <Box sx={{ display: 'flex' }}>
            <CssBaseline />
            <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
                <Toolbar>
                    <Typography variant="h6" noWrap component="div">
                        Authorisations Framework
                    </Typography>
                </Toolbar>
            </AppBar>
            <Sidebar />
            <Box component="main" sx={{ marginTop: "64px", p: 3 }}>
                {route.component && <route.component />}
            </Box>
        </Box>
    );
}


const Sidebar = () => {
    const currentPath = window.location.pathname;
    return (
        <Drawer
            variant="permanent"
            sx={{
                width: DRAWER_WIDTH,
                flexShrink: 0,
                [`& .MuiDrawer-paper`]: { width: DRAWER_WIDTH, boxSizing: 'border-box' },
            }}
        >
            <Toolbar />
            <Box sx={{ overflow: 'auto' }}>
                <List>
                    {
                        ROUTES.map((route) => (
                            <ListItem key={route.path} disablePadding divider={route.divider}>
                                <ListItemButton
                                    href={route.path}
                                    selected={currentPath === route.path}
                                >
                                    <ListItemIcon>{route.icon}</ListItemIcon>
                                    <ListItemText primary={route.label} />
                                </ListItemButton>
                            </ListItem>
                        ))
                    }
                </List>
            </Box>
        </Drawer>
    );
}