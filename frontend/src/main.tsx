// Polyfill support for old browsers
// https://github.com/vitejs/vite/issues/4786
// @ts-expect-error
import 'vite/modulepreload-polyfill';

import { ThemeProvider } from '@emotion/react';
import { createTheme } from '@mui/material';
import { LocalizationProvider } from '@mui/x-date-pickers';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import 'dayjs/locale/en-au';
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { RouterProvider } from 'react-router';
import SnackbarProvider from './context/Snackbar';
import './index.css';
import { router } from './router';
import DialogProvider from './context/Dialogs';


const theme = createTheme({
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
        },
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
