import { Alert, Snackbar, type AlertColor } from "@mui/material";
import { createContext, useContext, useState, type ReactNode } from "react";

// 1. Define the shape of the data your context will provide.
interface SnackbarContextType {
    showSnackbar: (message: ReactNode, severity?: AlertColor) => void;
}

// 2. Create the context with a default value.
const SnackbarContext = createContext<SnackbarContextType | undefined>(undefined);

// 3. Create a custom hook for easy access to the context.
export const useSnackbar = () => {
    const context = useContext(SnackbarContext);
    if (!context) {
        throw new Error("useSnackbar must be used within a SnackbarProvider");
    }
    return context;
};

// 4. Implement the provider to manage state and render the Snackbar.
export default function SnackbarProvider({ children }: { children: ReactNode }) {
    const [open, setOpen] = useState(false);
    const [message, setMessage] = useState<ReactNode>("");
    const [severity, setSeverity] = useState<AlertColor>("info");

    const showSnackbar = (newMessage: ReactNode, newSeverity: AlertColor = "info") => {
        setMessage(newMessage);
        setSeverity(newSeverity);
        setOpen(true);
    };

    const handleClose = (_?: React.SyntheticEvent | Event, reason?: string) => {
        if (reason === 'clickaway') {
            return;
        }
        setOpen(false);
    };

    const value = { showSnackbar };

    return (
        <SnackbarContext.Provider value={value}>
            {children}
            <Snackbar
                open={open}
                autoHideDuration={5000}
                onClose={handleClose}
                anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
            >
                {/* The Alert component provides the styling (color, icon) */}
                <Alert onClose={handleClose} severity={severity} sx={{ width: '100%' }} variant="filled">
                    {message}
                </Alert>
            </Snackbar>
        </SnackbarContext.Provider>
    );
}