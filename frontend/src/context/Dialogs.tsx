import CloseIcon from '@mui/icons-material/Close';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import IconButton from '@mui/material/IconButton';
import { styled } from '@mui/material/styles';
import { createContext, useContext, useState, type ReactNode } from "react";

// 1. Define the shape of the data your context will provide.
export interface DialogOptions {
    title: ReactNode;
    content: ReactNode;
    actions?: ReactNode;
}

interface DialogContextType {
    showDialog: (options: DialogOptions) => void;
    hideDialog: () => void;
}

// 2. Create the context with a default value that matches the type.
// This fixes the "Expected 1 arguments" error.
const DialogContext = createContext<DialogContextType | undefined>(undefined);

// 3. Create a custom hook for easy access to the context.
export const useDialog = () => {
    const context = useContext(DialogContext);
    if (!context) {
        throw new Error("useDialog must be used within a DialogProvider");
    }
    return context;
};

// 4. Implement the provider to manage state and render the dialog.
export default function DialogProvider({ children }: { children: ReactNode }) {
    const [options, setOptions] = useState<DialogOptions | null>(null);

    const showDialog = (newOptions: DialogOptions) => {
        setOptions(newOptions);
    };

    const hideDialog = () => {
        setOptions(null);
    };

    const value = { showDialog, hideDialog };

    return (
        <DialogContext.Provider value={value}>
            {children}

            {options && (
                <BootstrapDialog
                    onClose={hideDialog}
                    open={!!options}
                    aria-labelledby="customized-dialog-title"
                >
                    <DialogTitle sx={{ m: 0, p: 2 }} id="customized-dialog-title">
                        {options.title}
                        <IconButton
                            aria-label="close"
                            onClick={hideDialog}
                            sx={{ position: 'absolute', right: 8, top: 8, color: (theme) => theme.palette.grey[500] }}
                        >
                            <CloseIcon />
                        </IconButton>
                    </DialogTitle>
                    <DialogContent dividers>
                        {options.content}
                    </DialogContent>
                    {options.actions && (
                        <DialogActions>
                            {options.actions}
                        </DialogActions>
                    )}
                </BootstrapDialog>
            )}
        </DialogContext.Provider>
    );
}

const BootstrapDialog = styled(Dialog)(({ theme }) => ({
    '& .MuiDialogContent-root': {
        padding: theme.spacing(2),
    },
    '& .MuiDialogActions-root': {
        padding: theme.spacing(1),
    },
}));