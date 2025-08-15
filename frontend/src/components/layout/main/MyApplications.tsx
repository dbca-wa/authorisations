import DownloadRoundedIcon from '@mui/icons-material/DownloadRounded';
import PlayArrowRoundedIcon from '@mui/icons-material/PlayArrowRounded';
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import Typography from "@mui/material/Typography";
import dayjs from 'dayjs';
import relativeTime from "dayjs/plugin/relativeTime";
import { redirect, useLoaderData, useNavigate } from "react-router";
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
    // Format dates
    dayjs.extend(relativeTime)
    const createdAtRelative = dayjs(application.created_at).fromNow()
    const updatedAtRelative = dayjs(application.updated_at).fromNow()

    const navigate = useNavigate();

    return (
        <ListItem sx={{ marginBottom: 2 }}>
            <Card className="p-8 w-full" elevation={4} sx={{ borderRadius: 2 }}>
                <Typography variant="h6">{application.questionnaire_name}</Typography>
                <Typography variant="subtitle2" color="textSecondary" gutterBottom>
                    Created {createdAtRelative} <br />
                    Updated {updatedAtRelative}
                </Typography>
                <Typography variant="body1" color="textPrimary" gutterBottom>
                    {application.status}
                </Typography>
                <Box display="flex" justifyContent="flex-end" mt={2}>
                    <Button
                        variant="contained"
                        color="primary"
                        loadingPosition='start'
                        loading={false}
                        disabled={Boolean(false)}
                        startIcon={<PlayArrowRoundedIcon />}
                        onClick={() => navigate(`/a/${application.key}`)}
                    >
                        Continue
                    </Button>
                    <Button
                        variant="outlined"
                        color="secondary"
                        loadingPosition='start'
                        loading={false}
                        disabled={Boolean(false)}
                        startIcon={<DownloadRoundedIcon />}
                        onClick={() => {
                            console.log("Downloading certificate for:", application.key);
                        }}
                        sx={{ marginLeft: 2 }}
                    >
                        Certificate
                    </Button>
                </Box>
            </Card>
        </ListItem>


    )
}