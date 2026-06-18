import AppBar from '@mui/material/AppBar';
import BottomNavigation from '@mui/material/BottomNavigation';
import BottomNavigationAction from '@mui/material/BottomNavigationAction';
import Box from '@mui/material/Box';
import CssBaseline from '@mui/material/CssBaseline';
import Drawer from '@mui/material/Drawer';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Paper from '@mui/material/Paper';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';

import { useEffect, useMemo } from 'react';
import { useLoaderData, useNavigate, type NavigateFunction, type NavigateOptions } from 'react-router';
import { ConfigManager } from '../../../context/ConfigManager';
import { DRAWER_WIDTH } from '../../../context/Constants';
import type { IRoute, LoaderData } from "../../../context/types/Generic";
import type { IAuthorisationProcess } from '../../../context/types/Questionnaire';
import { ROUTES } from '../../../router';
import { Confetti } from '../../../context/Confetti';


export const MainLayout = ({
    route,
}: {
    route: IRoute,
}) => {
    const currentPath = window.location.pathname;
    const navOptions: NavigateOptions = { viewTransition: true };

    // Update page title
    useEffect(() => {
        document.title = `${route.label} : DBCA Authorisations`;
    }, [route.label]);

    const { processes } = useLoaderData<LoaderData>();
    const navigate: NavigateFunction = useNavigate();

    const footerRoutes = useMemo(
        () => ROUTES.filter((currentRoute) => {
            const isVisible = !currentRoute.condition || currentRoute.condition(processes);
            return currentRoute.sidebar === false && isVisible;
        }),
        [processes],
    );

    const selectedFooterRoute = footerRoutes.find((footerRoute) => !footerRoute.external && footerRoute.path === currentPath)?.path ?? "";

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
            <Sidebar processes={processes} />
            <Box component="main" sx={{ marginTop: "64px", p: 3, pb: '88px', flexGrow: 1 }}>
                {route.component && <route.component />}
            </Box>

            <Paper
                elevation={3}
                sx={{
                    position: 'fixed',
                    bottom: 0,
                    left: 0,
                    right: 0,
                    zIndex: (theme) => theme.zIndex.drawer + 1,
                }}
            >
                <BottomNavigation showLabels value={selectedFooterRoute}>
                    {footerRoutes.map((footerRoute) => (
                        <BottomNavigationAction
                            key={footerRoute.path}
                            label=""
                            aria-label={footerRoute.label}
                            icon={(
                                <Box sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.75 }}>
                                    {footerRoute.icon}
                                    <Typography component="span" variant="body2">
                                        {footerRoute.label}
                                    </Typography>
                                </Box>
                            )}
                            value={footerRoute.external ? `external:${footerRoute.path}` : footerRoute.path}
                            sx={{
                                minWidth: 'auto',
                                px: 2,
                                '& .MuiBottomNavigationAction-label': {
                                    display: 'none',
                                },
                            }}
                            onClick={() => footerRoute.external
                                ? window.open(footerRoute.path)
                                : navigate(footerRoute.path, navOptions)
                            }
                        />
                    ))}
                </BottomNavigation>
            </Paper>
        </Box>
    );
}


const Sidebar = ({
    processes,
}: {
    processes: IAuthorisationProcess[];
}) => {
    const currentPath = window.location.pathname;
    const navOptions: NavigateOptions = { viewTransition: true };
    const navigate: NavigateFunction = useNavigate();
    const appVersion = ConfigManager.get().app_version;

    const visibleRoutes = useMemo(
        () => ROUTES.filter((route) => route.sidebar !== false && (!route.condition || route.condition(processes))),
        [processes],
    );

    return (
        <Drawer
            variant="permanent"
            sx={{
                width: DRAWER_WIDTH,
                flexShrink: 0,
                [`& .MuiDrawer-paper`]: {
                    width: DRAWER_WIDTH,
                    boxSizing: 'border-box',
                    display: 'flex',
                    flexDirection: 'column',
                },
            }}
        >
            <Toolbar />
            <Box sx={{ overflow: 'auto', flexGrow: 1 }}>
                <List>
                    {
                        visibleRoutes.map((route) => {
                            return (
                                <ListItem key={route.path} disablePadding divider={route.divider}>
                                    <ListItemButton
                                        onClick={() => route.external
                                            // External routes (e.g. mailto:) must not go through React Router.
                                            ? window.open(route.path)
                                            : navigate(route.path, navOptions)
                                        }
                                        selected={!route.external && currentPath === route.path}
                                    >
                                        <ListItemIcon>{route.icon}</ListItemIcon>
                                        <ListItemText primary={route.label} />
                                    </ListItemButton>
                                </ListItem>
                            );
                        })
                    }
                </List>
            </Box>
            <Confetti celebrate={10}>{appVersion}</Confetti>
        </Drawer>
    );
}
