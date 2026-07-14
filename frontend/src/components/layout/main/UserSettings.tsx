import EngineeringIcon from "@mui/icons-material/Engineering";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

/**
 * User settings page placeholder component.
 * Displays an under-construction message while settings features are being implemented.
 */
export const UserSettings = () => {
    return (
        <Box className="p-8 w-full min-w-4xl lg:w-4xl xl:w-5xl 2xl:w-6xl">
            <Typography variant="h4" gutterBottom>
                Settings
            </Typography>
            <Typography color="textSecondary" sx={{ mb: 8 }}>
                Manage your account preferences and settings.
            </Typography>

            <Box className="flex flex-col items-center justify-center w-full gap-4 py-32">
                <EngineeringIcon sx={{ fontSize: 96, color: "text.secondary" }} />
                <Typography variant="h5" color="textSecondary" sx={{ mt: 2 }}>
                    We're building something great here!
                </Typography>
                <Typography variant="body1" color="textSecondary">
                    Settings are still under construction. Check back soon.
                </Typography>
            </Box>
        </Box>
    );
};
