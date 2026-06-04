import Alert from "@mui/material/Alert";
import Snackbar from "@mui/material/Snackbar";

import type { AlertColor } from "@mui/material/Alert";
import { useCallback, useState, type ReactNode } from "react";
import { SnackbarContext } from './SnackbarContext';

interface SnackbarNotification {
    id: number;
    message: ReactNode;
    severity: AlertColor;
    /** Drives MUI's open/close transition; set to false to play the exit animation. */
    open: boolean;
}

let nextNotificationId = 0;

// Approximate rendered height of each notification + gap between them.
const NOTIFICATION_STRIDE = 68;
const NOTIFICATION_BASE_BOTTOM = 16;

export const SnackbarProvider = ({ children }: { children: ReactNode }) => {
    const [notifications, setNotifications] = useState<SnackbarNotification[]>([]);

    /** Sets open=false to trigger MUI's exit animation; the item stays in the array until onExited fires. */
    const dismiss = useCallback((id: number) => {
        setNotifications((prev) => prev.map((n) => n.id === id ? { ...n, open: false } : n));
    }, []);

    /** Removes the item from the array after its exit animation has completed. */
    const remove = useCallback((id: number) => {
        setNotifications((prev) => prev.filter((n) => n.id !== id));
    }, []);

    /**
     * Adds a new notification to the bottom of the stack and schedules auto-dismissal.
     * Errors stay visible longer to give users time to read them.
     */
    const showSnackbar = useCallback((message: ReactNode, severity: AlertColor = "info") => {
        const id = nextNotificationId++;
        setNotifications((prev) => [...prev, { id, message, severity, open: true }]);
    }, []);

    return (
        <SnackbarContext.Provider value={{ showSnackbar }}>
            {children}

            {notifications.map((notification, index) => (
                <Snackbar
                    key={notification.id}
                    open={notification.open}
                    autoHideDuration={notification.severity === "success" ? 4000 : 8000}
                    onClose={(_, reason) => { if (reason !== "clickaway") dismiss(notification.id); }}
                    anchorOrigin={{ vertical: "bottom", horizontal: "left" }}
                    // Stack upward: newest at the base, older ones stack above.
                    // CSS transition smooths repositioning when a lower item is dismissed.
                    sx={{
                        bottom: `${NOTIFICATION_BASE_BOTTOM + (notifications.length - 1 - index) * NOTIFICATION_STRIDE}px !important`,
                        transition: "bottom 0.3s ease",
                    }}
                    slotProps={{ transition: { onExited: () => remove(notification.id) } }}
                >
                    <Alert
                        onClose={() => dismiss(notification.id)}
                        severity={notification.severity}
                        variant="filled"
                        sx={{ width: "100%" }}
                    >
                        {notification.message}
                    </Alert>
                </Snackbar>
            ))}
        </SnackbarContext.Provider>
    );
};