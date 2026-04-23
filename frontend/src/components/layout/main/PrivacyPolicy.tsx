import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import { PrivacyContent } from "./PrivacyContent";

/**
 * Renders the standalone privacy policy page content for navigation routes.
 */
export const PrivacyPolicy = () => {
    return (
        <Box sx={{ maxWidth: 960 }}>
            <Typography variant="h4" gutterBottom>
                Privacy Policy
            </Typography>
            <PrivacyContent />
        </Box>
    );
};
