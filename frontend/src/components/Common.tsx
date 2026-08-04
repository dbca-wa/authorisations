import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import NumbersIcon from '@mui/icons-material/Numbers';
import Box from "@mui/material/Box";
import Button from '@mui/material/Button';
import Grid from '@mui/material/Grid';
import IconButton from '@mui/material/IconButton';
import Link from '@mui/material/Link';
import TextField from '@mui/material/TextField';
import Tooltip from '@mui/material/Tooltip';
import Typography from "@mui/material/Typography";

import type { TypographyProps } from "@mui/material/Typography";
import { useRef } from 'react';
import { ApiManager } from '../context/ApiManager';
import { useDialog, useSnackbar } from '../context/Hooks';
import type { IApplicationAttachment } from "../context/types/Application";
import { getIconFromFilename } from "../context/Utils";


export const FileAttachmentList = ({
    attachments,
    canEdit = false,
    fullWidth = false,
    onAttachmentDeleted,
    onAttachmentUpdated,
}: {
    attachments: IApplicationAttachment[];
    canEdit?: boolean;
    fullWidth?: boolean;
    onAttachmentDeleted?: (attachmentKey: string) => void;
    onAttachmentUpdated?: (updatedAttachment: IApplicationAttachment) => void;
}) => {
    // Confirm dialog for delete action
    const { showDialog, hideDialog } = useDialog();

    // Snackbar for notifications
    const { showSnackbar } = useSnackbar();

    // Ref for the rename input (single ref works since only one dialog open at a time)
    const renameInputRef = useRef<HTMLInputElement>(null);

    const deleteAttachment = (attachment: IApplicationAttachment) => {
        showDialog({
            title: "Confirm deletion",
            content:
                <Box className="flex flex-col items-center justify-center px-4 gap-2">
                    <Typography sx={{ textAlign: "center" }}>Are you sure you want to delete the attachment<br />
                        <strong>{attachment.name}</strong>?
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
                                    const responseData = error.response?.data as { detail?: string } | undefined;
                                    const message = responseData?.detail ?? error.message;
                                    showSnackbar(`Failed to delete file: ${message}`, "error");
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

        // Helper function to perform the rename action
        const performRename = () => {
            const newBaseName = (renameInputRef.current?.value || baseName).trim();
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
        };

        showDialog({
            title: "Rename attachment",
            content:
                <Box className="w-md items-center justify-center flex flex-col gap-2">
                    <Box className="flex items-end gap-1 w-full">
                        <TextField
                            inputRef={renameInputRef}
                            defaultValue={baseName}
                            label="File name"
                            variant="standard"
                            fullWidth
                            onKeyDown={(e) => {
                                // Trigger rename on Enter key
                                if (e.key === 'Enter') {
                                    e.preventDefault();
                                    performRename();
                                }
                            }}
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
                    onClick={performRename}
                >
                    Rename
                </Button>
            ),
            onOpen: () => {
                renameInputRef.current?.focus();
            }
        });
    }

    // Adjust min height if edit actions are visible
    const minHeight = canEdit ? "min-h-54" : "min-h-40";
    
    // Dynamically adjust item size based on attachment count
    const itemCount = attachments.length;
    const justifyContent = fullWidth && itemCount < 6 ? 'space-around' : 'flex-start';
    const size = fullWidth && itemCount < 6
        ? itemCount <= 2
            ? { xs: 6, sm: 5, md: 4.5, lg: 4.5, xl: 4.5 }  // Make 1-2 items wider but not full width
            : itemCount === 3
            ? { xs: 6, sm: 4, md: 3, lg: 3, xl: 3 }  // 3 items at reasonable width
            : itemCount === 4
            ? { xs: 6, sm: 4, md: 3, lg: 3, xl: 3 }  // 4 items fills the row
            : { xs: 6, sm: 4, md: 3, lg: 2.4, xl: 2.4 }  // 5 items
        : { xs: 6, sm: 4, md: 3, lg: 2.4, xl: 2 };

    return (
        <Grid container spacing={2} sx={{ alignItems: 'stretch', justifyContent: justifyContent }} className="min-w-sm!">
            {attachments.map((attachment) => (
                <Grid key={attachment.key}
                    size={size}
                    className={`rounded-md flex flex-col items-center justify-between py-2 px-2 ${minHeight}`}
                    sx={{
                        border: '1px solid',
                        borderColor: 'action.disabled',
                        '&:hover': {
                            borderColor: 'primary.main',
                        }
                    }}
                >
                    <Tooltip title={attachment.name}>
                        <Link
                            href={attachment.download_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            underline="none"
                            className="flex flex-col items-center gap-2 w-full"
                        >
                            {getIconFromFilename(attachment.name)}
                            <Typography variant="body2" className="text-center w-full wrap-break-word line-clamp-3">
                                {attachment.name}
                            </Typography>
                        </Link>
                    </Tooltip>
                    {canEdit && (
                        <Box className="flex gap-2">
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
                </Grid>
            ))}
        </Grid>
    );
};


/**
 * Displays an application internal ID with copy-to-clipboard functionality.
 * Shows icon + ID and provides hover feedback and snackbar notifications.
 * Adapts styling based on the variant for use in different contexts.
 */
export const ApplicationIdDisplay = ({
    internalId,
    variant = "caption",
}: {
    internalId: string;
    variant?: TypographyProps['variant'];
}) => {
    const { showSnackbar } = useSnackbar();

    const handleCopy = () => {
        navigator.clipboard.writeText(`#${internalId}`)
            .then(() => {
                showSnackbar('Application ID copied to clipboard', 'info');
            })
            .catch(() => {
                showSnackbar('Failed to copy to clipboard', 'error');
            });
    };

    // Determine styling based on variant
    const isSmallVariant = variant === 'caption' || variant === 'body2';

    return (
        <Tooltip title="Copy application ID" placement="top" arrow>
            <Typography
                variant={variant}
                component="div"
                className="flex items-center w-fit cursor-pointer transition-opacity duration-200 ease-in-out hover:opacity-100"
                sx={{
                    opacity: isSmallVariant ? 0.7 : 1,
                }}
                onClick={handleCopy}
            >
                <NumbersIcon sx={{ fontSize: 'inherit' }} />
                {internalId}
            </Typography>
        </Tooltip>
    );
};
