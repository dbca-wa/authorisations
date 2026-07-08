import SentimentNeutralIcon from '@mui/icons-material/SentimentNeutral';
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

/**
 * Empty state component for displaying when no items are available.
 * Uses Tailwind for styling and includes a touch of humour.
 */
export const EmptyStateComponent = () => {
    return (
        <Box className="flex flex-col items-center justify-center w-full min-w-2xl gap-4 py-32">
            <SentimentNeutralIcon sx={{ fontSize: 96, color: "text.secondary" }} />
            <Typography variant="h5" color="textSecondary" sx={{ mt: 2 }}>
                Nothing to see here
            </Typography>
            <Typography variant="body1" color="textSecondary" sx={{ maxWidth: "400px", textAlign: "center" }}>
                We checked. There really isn't anything hiding here.
            </Typography>
        </Box>
    );
}