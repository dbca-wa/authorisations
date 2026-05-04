import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import Box from "@mui/material/Box";
import Button from '@mui/material/Button';
import Grid from '@mui/material/Grid';
import IconButton from '@mui/material/IconButton';
import Link from '@mui/material/Link';
import TextField from '@mui/material/TextField';
import Typography from "@mui/material/Typography";

import { useEffect, useRef, useState } from 'react';
import { ApiManager } from '../context/ApiManager';
import { useDialog } from '../context/Dialogs';
import { useSnackbar } from '../context/Snackbar';
import { getIconFromFilename } from "../context/Utils";
import type { IApplicationAttachment } from "../context/types/Application";


/**
 * Resolves a deferred promise from a route loader into component state.
 *
 * Data-agnostic: the hook does not know or care whether it is handling
 * applications, questionnaires, or any other resource type. The calling
 * component owns the type and the initial (empty) value.
 *
 * Returns a [resolvedValue, isLoading] tuple that mirrors the useState
 * pair it replaces, so call-sites stay readable and minimal.
 */
export function useResolvedPromise<T>(
    promise: Promise<T> | undefined,
    initialValue: T,
): [T, boolean] {
    // Capture the initial value in a ref so it never causes the effect to
    // re-run when the caller passes an inline literal (e.g. [] or {}).
    const initialValueRef = useRef<T>(initialValue);
    const [value, setValue] = useState<T>(initialValue);
    // Start as loading only when a promise is actually provided, avoiding a
    // spurious loading flash on routes that omit this data.
    const [isLoading, setIsLoading] = useState<boolean>(promise !== undefined);

    useEffect(() => {
        if (!promise) {
            setIsLoading(false);
            return;
        }

        // Guard flag: prevents state updates if the component unmounts before the promise settles.
        let isMounted = true;
        setIsLoading(true);

        promise
            .then((resolved) => {
                if (!isMounted) return;
                setValue(resolved);
            })
            .catch(() => {
                // Fall back to the initial value so the empty-state UI can render safely.
                if (!isMounted) return;
                setValue(initialValueRef.current);
            })
            .finally(() => {
                if (!isMounted) return;
                setIsLoading(false);
            });

        return () => {
            isMounted = false;
        };
    }, [promise]);

    return [value, isLoading];
}


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
    const renameInputRef = useRef<HTMLInputElement>(null);

    const deleteAttachment = (attachment: IApplicationAttachment) => {
        showDialog({
            title: "Confirm Deletion",
            content:
                <Box
                    sx={{
                        alignItems: "center",
                        justifyContent: "center",
                        display: "flex",
                        flexDirection: "column",
                        px: 4,
                        gap: 2,
                    }}
                >
                    <Typography sx={{ textAlign: "center" }}>Are you sure you want to delete the attachment<br />
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
        };

        showDialog({
            title: "Rename Attachment",
            content:
                <Box className="w-md items-center justify-center flex flex-col gap-2">
                    <Box sx={{ display: "flex", alignItems: "flex-end", gap: 1, width: "100%" }}>
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

    return (
        <Box className="p-4 border border-gray-300 rounded-md">
            <Grid container spacing={2}>
                {attachments.map((attachment) => (
                    <Grid key={attachment.key} size={{ md: 3, lg: 2.4, xl: 2 }}>
                        <Box className="border border-gray-300 rounded-lg h-56 px-4 py-4 flex flex-col items-center">
                            <Link
                                href={attachment.download_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                underline="none"
                                className="flex flex-col items-center gap-2 h-full"
                            >
                                {getIconFromFilename(attachment.name)}
                                <Typography variant="body2" className="text-center w-28 line-clamp-3">
                                    {attachment.name}
                                </Typography>
                            </Link>
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
                        </Box>
                    </Grid>
                ))}
            </Grid>
        </Box>
    );
};
