import CloseIcon from '@mui/icons-material/Close';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import IconButton from '@mui/material/IconButton';

import { styled } from '@mui/material/styles';
import { useEffect, useState, type ReactNode } from "react";
import { DialogContext, type DialogOptions } from './DialogContext';

/**
 * Provides a shared dialog API and renders a single project-wide dialog host.
 *
 * Keeping the host centralised ensures all feature areas open/close dialogs
 * consistently without duplicating modal state in each page component.
 */
export const DialogProvider = ({ children }: { children: ReactNode }) => {
    const [options, setOptions] = useState<DialogOptions | null>(null);

    const showDialog = (newOptions: DialogOptions) => {
        setOptions(newOptions);
    };

    const hideDialog = () => {
        options?.onClose?.();
        setOptions(null);
    };

    // Fire onOpen after paint so focus-sensitive handlers run against mounted dialog content.
    useEffect(() => {
        if (options) {
            // requestAnimationFrame avoids race conditions with MUI portal/layout timing.
            requestAnimationFrame(() => {
                options.onOpen?.();
            });
        }
    }, [options]);

    const value = { showDialog, hideDialog };

    return (
        <DialogContext.Provider value={value}>
            {children}

            {options && (
                <BootstrapDialog
                    onClose={hideDialog}
                    open={!!options}
                    // fullWidth
                    maxWidth="lg"
                    aria-labelledby="customised-dialog-title"
                >
                    <DialogTitle sx={{ m: 0, p: 2 }} id="customised-dialog-title">
                        {options.title}
                        <IconButton
                            aria-label="close"
                            disabled={false}
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
                        <DialogActions style={{ justifyContent: "space-between" }}>
                            {options.actions}
                        </DialogActions>
                    )}
                </BootstrapDialog>
            )}
        </DialogContext.Provider>
    );
};

const BootstrapDialog = styled(Dialog)(({ theme }) => ({
    '& .MuiDialogContent-root': {
        padding: theme.spacing(2),
    },
    '& .MuiDialogActions-root': {
        padding: theme.spacing(1),
    },
}));