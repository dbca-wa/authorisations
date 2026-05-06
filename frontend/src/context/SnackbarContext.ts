import type { AlertColor } from '@mui/material/Alert';
import { createContext, type ReactNode } from 'react';

/**
 * Context contract for publishing UI notifications.
 */
export interface SnackbarContextType {
    showSnackbar: (message: ReactNode, severity?: AlertColor) => void;
}

/**
 * Shared snackbar context consumed by provider and hooks.
 */
export const SnackbarContext = createContext<SnackbarContextType | undefined>(undefined);
