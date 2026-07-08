import Box from "@mui/material/Box";
import CircularProgress from "@mui/material/CircularProgress";
import Typography from "@mui/material/Typography";

/**
 * Reusable loading state component.
 * Displays a spinner centered on the page while data is being fetched.
 * 
 * @example
 * {isLoading ? <LoadingState /> : <Content />}
 */
export const LoadingState = () => {
    return (
        <Box className="flex flex-col items-center justify-center w-full gap-6 py-64">
            <CircularProgress enableTrackSlot size={64} />
            <Typography variant="body1" color="textSecondary">
                One moment while we fetch that for you...
            </Typography>
        </Box>
    );
};
