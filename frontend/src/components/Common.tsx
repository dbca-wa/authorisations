import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import Box from "@mui/material/Box";
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import Link from '@mui/material/Link';
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { ApiManager } from '../context/ApiManager';
import { useDialog } from '../context/Dialogs';
import { useSnackbar } from '../context/Snackbar';
import { getIconFromFilename } from "../context/Utils";
import type { IApplicationAttachment } from "../context/types/Application";


export const FileAttachmentList = ({
    attachments,
    canDelete = false,
    onAttachmentDeleted,
}: {
    attachments: IApplicationAttachment[];
    canDelete?: boolean;
    onAttachmentDeleted?: (attachmentKey: string) => void;
}) => {
    // Confirm dialog for delete action
    const { showDialog, hideDialog } = useDialog();

    // Snackbar for notifications
    const { showSnackbar } = useSnackbar();

    const deleteAttachment = (attachment: IApplicationAttachment) => {
        showDialog({
            title: "Confirm Deletion",
            content: `Are you sure you want to delete the attachment "${attachment.name}"? ` +
                'This action cannot be undone.',
            actions: (
                <>
                    <Button
                        variant="contained"
                        color="error"
                        startIcon={<DeleteIcon />}
                        onClick={() => {
                            // Call the API to delete the attachment
                            ApiManager.deleteAttachment(attachment.key)
                                .then(() => {
                                    showSnackbar("File has been deleted", "success");
                                    onAttachmentDeleted?.(attachment.key);
                                })
                                .catch((error) => {
                                    console.error("Error deleting attachment:", error);
                                });

                            // Close the dialog after action
                            hideDialog();
                        }}
                    >
                        Delete attachment
                    </Button>
                </>
            ),
        });
    };

    const renameAttachment = (attachment: IApplicationAttachment) => {
        showDialog({
            title: "Rename Attachment",
            content: `Renaming is not implemented yet.`,
            actions: (
                <Button
                    variant="contained"
                    color="primary"
                    startIcon={<EditIcon />}
                    onClick={() => {
                        // Placeholder for rename functionality
                        alert(`Rename attachment: ${attachment.name}`);
                        hideDialog();
                    }}
                >
                    OK
                </Button>
            ),
        });
    }


    return (
        <Box className="p-4 border border-gray-300 rounded-md">
            <Stack direction="row" spacing={4} marginTop={2} justifyContent={"center"} alignItems={"center"} >
                {attachments.map((attachment) => (
                    <Box key={attachment.key} className="relative border border-gray-300 rounded-lg px-4 pb-8 flex flex-col items-center min-w-[120px]">
                        {canDelete && (
                            <Box className="absolute bottom-0 center-x-0 flex gap-1">
                                <IconButton
                                    color="error"
                                    size="small"
                                    title={`Delete: ${attachment.name}`}
                                    onClick={() => deleteAttachment(attachment)}
                                >
                                    <DeleteIcon fontSize="small" />
                                </IconButton>
                                <IconButton
                                    color="primary"
                                    size="small"
                                    title={`Rename: ${attachment.name}`}
                                    onClick={() => renameAttachment(attachment)}
                                >
                                    <EditIcon fontSize="small" />
                                </IconButton>
                            </Box>
                        )}
                        <Link
                            href={attachment.download_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            underline="none"
                            className="flex flex-col items-center gap-2"
                        >
                            {getIconFromFilename(attachment.name)}
                            <Typography variant="body2" style={{ wordBreak: 'break-word', textAlign: 'center', maxWidth: 120 }}>
                                {attachment.name}
                            </Typography>
                        </Link>
                    </Box>
                ))}
            </Stack>
        </Box>
    );
};
