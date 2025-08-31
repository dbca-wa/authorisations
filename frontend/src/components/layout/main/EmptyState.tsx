import SentimentDissatisfiedIcon from '@mui/icons-material/SentimentDissatisfied';
import { Box, Typography } from "@mui/material";

export const EmptyStateComponent = () => {
    return (
        <Box
            display="flex"
            flexDirection="column"
            alignItems="center"
            justifyContent="center"
            height="60vh"
        >
            <SentimentDissatisfiedIcon sx={{ fontSize: 60, mb: 2 }} />
            <Typography variant="h6" component="h2" gutterBottom>
                No items found
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                It looks like there's nothing here yet.
            </Typography>
        </Box>
    );
}