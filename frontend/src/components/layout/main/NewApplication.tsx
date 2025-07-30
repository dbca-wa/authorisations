import { Box, Button, Card, List, ListItem, Typography } from "@mui/material";
import { useLoaderData } from "react-router";
import type { IQuestionnaireData } from "../../../context/FormTypes";
import { EmptyStateComponent } from "./EmptyState";

export const NewApplication = () => {
    const questionnaires = useLoaderData<IQuestionnaireData[]>();
    // console.log('Questionnaires:', questionnaires);

    return (
        <Box className="p-8 min-w-4xl max-w-7xl">
            <Typography variant="h4" gutterBottom>
                Start a New Application
            </Typography>
            <p>Select a questionnaire to start a new application.</p>
            {questionnaires.length === 0 ? <EmptyStateComponent /> :
                <List>
                    {questionnaires.map((q) =>
                        <Questionnaire key={q.slug} questionnaire={q} />)}
                </List>
            }
        </Box>
    );
}

/** Display a MUI card the given questionnaire with a link to start a new application for it */
const Questionnaire = ({
    questionnaire,
}: {
    questionnaire: IQuestionnaireData;
}) => {
    const localDate = new Date(questionnaire.created_at).toLocaleDateString()

    return (
        <ListItem sx={{ marginBottom: 2 }}>
            <Card className="p-8 w-full" elevation={4} sx={{ borderRadius: 2 }}>
                <Typography variant="h6">{questionnaire.name}</Typography>
                <Typography variant="subtitle2" color="textSecondary" gutterBottom>
                    Last updated: {localDate} (v{questionnaire.version})
                </Typography>
                <Typography variant="body1" color="textPrimary" gutterBottom>
                    {questionnaire.description}
                </Typography>
                <Box display="flex" justifyContent="flex-end" mt={2}>
                    <Button
                        variant="contained"
                        color="info"
                        onClick={() => {
                            console.log("Starting application for:", questionnaire.name);
                        }}
                    >
                        Start Application
                    </Button>
                </Box>
            </Card>
        </ListItem>
    );
}
