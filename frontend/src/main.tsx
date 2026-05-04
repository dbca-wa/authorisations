// Polyfill support for old browsers
// https://github.com/vitejs/vite/issues/4786
import 'vite/modulepreload-polyfill';

import { ThemeProvider } from '@emotion/react';
import { createTheme } from '@mui/material/styles';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import 'dayjs/locale/en-au';
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { RouterProvider } from 'react-router';
import DialogProvider from './context/Dialogs';
import { SnackbarProvider } from './context/Snackbar';
import './index.css';
import { router } from './router';


const theme = createTheme({
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
        },
      },
    },
    MuiTab: {
      styleOverrides: {
        root: {
          textTransform: 'none',
        },
      },
    },
    MuiStepIcon: {
      styleOverrides: {
        root: ({ theme }) => ({
          '&.Mui-completed': {
            color: theme.palette.primary.light,
          },
          '&.Mui-active': {
            color: theme.palette.primary.main,
          },
          color: theme.palette.grey[400],
        }),
      },
    },
  },
});

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ThemeProvider theme={theme}>
      <LocalizationProvider dateAdapter={AdapterDayjs} adapterLocale="en-au">
        <DialogProvider>
          <SnackbarProvider>
            <RouterProvider router={router} />
          </SnackbarProvider>
        </DialogProvider>
      </LocalizationProvider>
    </ThemeProvider>
  </StrictMode>
)
