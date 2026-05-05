import { createContext, type ReactNode } from 'react';

/**
 * Runtime options that control the shared dialog presentation and lifecycle callbacks.
 */
export interface DialogOptions {
    title: ReactNode;
    content: ReactNode;
    actions?: ReactNode;
    onOpen?: () => void;
    onClose?: () => void;
}

/**
 * Context contract for opening and closing the shared dialog.
 */
export interface DialogContextType {
    showDialog: (options: DialogOptions) => void;
    hideDialog: () => void;
}

/**
 * Shared dialog context consumed by provider and hooks.
 */
export const DialogContext = createContext<DialogContextType | undefined>(undefined);
