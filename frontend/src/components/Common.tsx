import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import Box from "@mui/material/Box";
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import Link from '@mui/material/Link';
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import React from 'react';

import { TextField } from '@mui/material';
import { ApiManager } from '../context/ApiManager';
import { useDialog } from '../context/Dialogs';
import { useSnackbar } from '../context/Snackbar';
import { getIconFromFilename } from "../context/Utils";
import type { IApplicationAttachment } from "../context/types/Application";


export const FileAttachmentList = ({
    attachments,
    canEdit = false,
    onAttachmentDeleted,
    onAttachmentUpdated,
}: {
    attachments: IApplicationAttachment[];
    canEdit?: boolean;
    onAttachmentDeleted?: (attachmentKey: string) => void;
    onAttachmentUpdated?: (updatedAttachment: IApplicationAttachment) => void;
}) => {
    // Confirm dialog for delete action
    const { showDialog, hideDialog } = useDialog();

    // Snackbar for notifications
    const { showSnackbar } = useSnackbar();

    // Ref for the rename input (single ref works since only one dialog open at a time)
    const renameInputRef = React.useRef<HTMLInputElement>(null);

    const deleteAttachment = (attachment: IApplicationAttachment) => {
        showDialog({
            title: "Confirm Deletion",
            content:
                <Box alignItems="center" justifyContent="center"
                    display="flex" flexDirection="column" paddingX={4} gap={2}>
                    <Typography textAlign={"center"}>Are you sure you want to delete the attachment<br />
                        <strong>{attachment.name}</strong> ?
                    </Typography>
                    <Typography>This action cannot be undone.</Typography>
                </Box>,
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
                                    // Notify parent about deletion
                                    onAttachmentDeleted?.(attachment.key);
                                    showSnackbar("File has been deleted", "success");
                                })
                                .catch((error) => {
                                    console.error("Error deleting attachment:", error);
                                });

                            // Close the dialog after action
                            hideDialog();
                        }}
                    >
                        Delete
                    </Button>
                </>
            ),
        });
    };

    const renameAttachment = (attachment: IApplicationAttachment) => {
        // Split filename and extension
        const lastDotIndex = attachment.name.lastIndexOf('.');
        const baseName = lastDotIndex === -1 ? attachment.name : attachment.name.substring(0, lastDotIndex);
        const extension = lastDotIndex === -1 ? '' : attachment.name.substring(lastDotIndex);

        showDialog({
            title: "Rename Attachment",
            content:
                <Box className="w-md items-center justify-center flex flex-col gap-2">
                    <Box display="flex" alignItems="flex-end" gap={1} width="100%">
                        <TextField
                            inputRef={renameInputRef}
                            defaultValue={baseName}
                            label="File name"
                            variant="standard"
                            fullWidth
                        />
                        {extension && (
                            <Typography variant="body1" style={{ whiteSpace: 'nowrap', paddingBottom: 8 }}>
                                {extension}
                            </Typography>
                        )}
                    </Box>
                </Box>,
            actions: (
                <Button
                    variant="contained"
                    color="primary"
                    startIcon={<EditIcon />}
                    onClick={() => {
                        const newBaseName = renameInputRef.current?.value || baseName;
                        const newFullName = newBaseName + extension;

                        // Call the API to rename the attachment
                        ApiManager.renameAttachment(attachment.key, newFullName)
                            .then((updatedAttachment) => {
                                // Notify parent with updated attachment
                                onAttachmentUpdated?.(updatedAttachment);
                                showSnackbar("File has been renamed", "success");
                            })
                            .catch((error) => {
                                console.error("Error renaming attachment:", error);
                            });

                        // Close the dialog after action
                        hideDialog();
                    }}
                >
                    Rename
                </Button>
            ),
        });
    }

    return (
        <Box className="p-4 border border-gray-300 rounded-md">
            <Stack direction="row" spacing={4} marginTop={2} justifyContent={"center"} alignItems={"center"} >
                {attachments.map((attachment) => (
                    <Box key={attachment.key} className="relative border border-gray-300 rounded-lg px-4 pb-8 flex flex-col items-center min-w-[120px]">
                        {canEdit && (
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
