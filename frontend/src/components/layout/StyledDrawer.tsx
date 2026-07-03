import MuiDrawer from '@mui/material/Drawer';

import { styled, type CSSObject, type Theme } from '@mui/material/styles';


const drawerWidths = {
    base: 240,
    lg: 280,
    xl: 320,
} as const;

const responsiveOpenWidth = (theme: Theme): CSSObject => ({
    width: drawerWidths.base,
    [theme.breakpoints.up('lg')]: {
        width: drawerWidths.lg,
    },
    [theme.breakpoints.up('xl')]: {
        width: drawerWidths.xl,
    },
});

const openedMixin = (theme: Theme): CSSObject => ({
    ...responsiveOpenWidth(theme),
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

export const openDrawerOffsetMixin = (theme: Theme): CSSObject => ({
    marginLeft: drawerWidths.base,
    width: `calc(100% - ${drawerWidths.base}px)`,
    [theme.breakpoints.up('lg')]: {
        marginLeft: drawerWidths.lg,
        width: `calc(100% - ${drawerWidths.lg}px)`,
    },
    [theme.breakpoints.up('xl')]: {
        marginLeft: drawerWidths.xl,
        width: `calc(100% - ${drawerWidths.xl}px)`,
    },
});

export const ResponsivePermanentDrawer = styled(MuiDrawer)(({ theme }) => ({
    ...responsiveOpenWidth(theme),
    flexShrink: 0,
    boxSizing: 'border-box',
    '& .MuiDrawer-paper': {
        ...responsiveOpenWidth(theme),
        boxSizing: 'border-box',
        display: 'flex',
        flexDirection: 'column',
    },
}));

export const ResponsiveMiniDrawer = styled(MuiDrawer, {
    shouldForwardProp: (prop) => prop !== 'open',
})<{ open?: boolean }>(({ theme, open }) => ({
    ...responsiveOpenWidth(theme),
    flexShrink: 0,
    boxSizing: 'border-box',
    ...(open
        ? {
            ...openedMixin(theme),
            '& .MuiDrawer-paper': openedMixin(theme),
        }
        : {
            ...closedMixin(theme),
            '& .MuiDrawer-paper': closedMixin(theme),
        }),
}));