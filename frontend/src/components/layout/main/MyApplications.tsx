import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import Typography from "@mui/material/Typography";
import { useLoaderData } from "react-router";
import type { IApplicationData } from "../../../context/types/Application";
import { EmptyStateComponent } from "./EmptyState";



export const MyApplications = () => {
    const applications = useLoaderData<IApplicationData[]>();
    // console.log('Applications:', applications);

    return (
        <Box className="p-8 min-w-4xl max-w-7xl">
            <Typography variant="h4" gutterBottom>
                My Applications
            </Typography>
            <p>Here you can view and manage your applications.</p>

            {applications.length === 0 ? <EmptyStateComponent /> :
                <List>
                    {applications.map((a) =>
                        <Application key={a.key} application={a} />)}
                </List>
            }
        </Box>
    );
}

/** Display a MUI card for an application with action buttons; to resume or to download its certificate */
const Application = ({
    application,
}: {
    application: IApplicationData;
}) => {
    return (
        <ListItem>
            <Box className="p-8 w-full" sx={{ borderRadius: 2 }}>
                <Typography variant="h6">{application.key}</Typography>
                <Typography variant="subtitle2" color="textSecondary" gutterBottom>
                    {application.created_at}
                </Typography>
                <Typography variant="body1" color="textPrimary" gutterBottom>
                    {application.status}
                </Typography>
                <Box display="flex" justifyContent="flex-end" mt={2}>
                    <Button
                        variant="contained"
                        color="primary"
                        onClick={() => {
                            console.log("Resuming application:", application.key);
                        }}
                    >
                        Resume Application
                    </Button>
                    <Button
                        variant="outlined"
                        color="secondary"
                        onClick={() => {
                            console.log("Downloading certificate for:", application.key);
                        }}
                        sx={{ marginLeft: 2 }}
                    >
                        Download Certificate
                    </Button>
                </Box>
            </Box>
        </ListItem>
    )
}