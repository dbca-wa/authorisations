import BlockIcon from '@mui/icons-material/Block';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import DriveFolderUploadIcon from '@mui/icons-material/DriveFolderUpload';
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import FormHelperText from "@mui/material/FormHelperText";
import LinearProgress from '@mui/material/LinearProgress';
import Typography from '@mui/material/Typography';
import React from 'react';

import type { AlertColor } from '@mui/material/Alert';
import type { AxiosError, AxiosProgressEvent } from 'axios';
import { useDropzone } from 'react-dropzone';
import { Controller, type ControllerRenderProps, type FieldValues } from "react-hook-form";
import { ApiManager } from '../../context/ApiManager';
import { ConfigManager } from '../../context/ConfigManager';
import { ERROR_MSG } from "../../context/Constants";
import { useSnackbar } from '../../context/Snackbar';
import type { IApplicationAttachment } from '../../context/types/Application';
import type { Question } from "../../context/types/Questionnaire";
import { VisuallyHiddenInput } from '../../context/Utils';
import { FileAttachmentList } from '../Common';

// Initially we start with allowing only 1 file per question to keep things simple.
// But later on, we may extend this functionality to allow multiple files with minor UI changes.
const MAX_FILES_PER_QUESTION = 1;

export const FileInput = ({
    question,
    attachments: initialAttachments,
    applicationKey,
}: {
    question: Readonly<Question>;
    attachments: IApplicationAttachment[];
    applicationKey: string;
}) => {
    // Local state to manage attachments (add/remove without parent coordination)
    const [attachments, setAttachments] = React.useState<IApplicationAttachment[]>(initialAttachments);

    // Abort controlller to allow cancelling
    const controller = new AbortController();

    const onAttachmentAdded = (newAttachment: IApplicationAttachment) => {
        setAttachments(prev => [...prev, newAttachment]);
    };

    const onAttachmentDeleted = (attachmentKey: string) => {
        setAttachments(prev => prev.filter(att => att.key !== attachmentKey));
    };

    const onAttachmentRenamed = (updatedAttachment: IApplicationAttachment) => {
        setAttachments(prev =>
            prev.map(att => att.key === updatedAttachment.key ? updatedAttachment : att)
        );
    };

    // Snackbar for notifications
    const { showSnackbar } = useSnackbar();

    return <Controller
        name={question.key}
        // React controlled vs uncontrolled warning fix:
        // This registers the field with an empty string if no
        // value is provided in the form's defaultValues. This ensures the
        // submitted data contains an empty string instead of undefined.
        defaultValue={""}
        rules={{
            required: question.o.is_required ? ERROR_MSG.required : false,
        }}
        render={({ field, fieldState }) => {
            // console.log("field:", field);

            return (
                <Box className="w-full">
                    <Typography variant="h6">
                        {question.labelText}
                    </Typography>
                    <Typography variant="subtitle1">
                        {question.o.description}
                    </Typography>
                    {/* Display the tiled attachment list if there are attachments */}
                    {attachments.length > 0 &&
                        FileAttachmentList({
                            attachments: attachments, canEdit: true,
                            onAttachmentDeleted: onAttachmentDeleted,
                            onAttachmentRenamed: onAttachmentRenamed,
                        })
                    }
                    {/* Show the dropzone if we have less than the max allowed files for this question */}
                    {attachments.length < MAX_FILES_PER_QUESTION &&
                        <DropzoneDialogContent
                            applicationKey={applicationKey}
                            field={field}
                            signal={controller.signal}
                            showSnackbar={showSnackbar}
                            onAttachmentAdded={onAttachmentAdded}
                        />
                    }
                    {fieldState.invalid &&
                        <FormHelperText error>
                            {fieldState.error?.message}
                        </FormHelperText>
                    }
                </Box>
            );
        }}
    />
}


const DropzoneDialogContent = ({
    applicationKey,
    field,
    signal,
    showSnackbar,
    onAttachmentAdded,
}: {
    applicationKey: string;
    field: ControllerRenderProps<FieldValues, string>;
    signal: AbortSignal;
    showSnackbar: (message: React.ReactNode, severity?: AlertColor) => void;
    onAttachmentAdded: (newAttachment: IApplicationAttachment) => void;
}) => {
    // The name of the file being uploaded
    const [filename, setFilename] = React.useState<string | null>(null);
    // Uploading progress state (0-100) or null (not uploading yet)
    const [progress, setProgress] = React.useState<number | null>(null);
    // Ref to hold pending reset timer id so we can clear it on unmount
    const resetTimerRef = React.useRef<number | null>(null);

    /**
     * Resets the dropzone state to allow user to try uploading again.
     */
    const Reset = React.useCallback((delay: number = 3) => {
        // Delay the reset for visual feedback
        if (delay > 0) {
            // clear any existing timer first
            if (resetTimerRef.current) {
                clearTimeout(resetTimerRef.current);
            }
            // schedule a new timer and store id so we can cancel on unmount
            resetTimerRef.current = window.setTimeout(() => Reset(0), delay * 1000) as unknown as number;
            return;
        }

        // clear UI state
        setFilename(null);
        setProgress(null);
    }, []);

    // Clear any pending timeout when the component unmounts to avoid updating
    // state after unmount (prevents React warnings / potential leaks).
    React.useEffect(() => {
        return () => {
            if (resetTimerRef.current) {
                clearTimeout(resetTimerRef.current);
                resetTimerRef.current = null;
            }
        };
    }, []);

    /**
     * Handles the file drop event, uploads the file via API, and updates the form state.
     */
    const onDrop = React.useCallback(async (acceptedFiles: File[], fileRejections: any[]) => {
        // Dropped file(s) has been rejected - we want exactly 1 accepted file.
        if (acceptedFiles.length !== 1 || fileRejections.length !== 0) {
            // console.debug("File drop rejected", { acceptedFiles, fileRejections });
            const message = fileRejections[0]?.errors?.[0]?.message ??
                "File is rejected. Please ensure it meets the requirements.";
            showSnackbar(message, "error");
            Reset(3);
            return;
        }

        const file = acceptedFiles[0];
        setFilename(file.name);
        // console.log("File selected:", file);

        // Start uploading the file via API
        const response = await ApiManager.uploadAttachment({
            appKey: applicationKey,
            name: file.name,
            question: field.name,
            file: file,
            signal: signal,
            callback: (event: AxiosProgressEvent) => {
                // console.log("Upload progress:", event)
                // Update the progress percentage
                if (event.progress) setProgress(event.progress * 100);
            },
        })
            // Successfully uploaded via API
            .then((resp) => {
                showSnackbar("File has been uploaded", "success");
                onAttachmentAdded(resp);
                return resp;
            })
            // Display the error message to user and log to console
            .catch((error: AxiosError) => {
                console.error('API Error:', error);
                const responseData = error.response?.data as any;
                const message = responseData?.file?.[0]
                    ?? error.message;
                showSnackbar(`Failed to upload: ${message}`, "error");
                return null;
            })
            // Reset the state so user can try uploading again (up to the max limit).
            .finally(() => Reset(3));

        // Something went terribly wrong with the upload, i.e. network error.
        if (!response) return;

        // We may update react-hook-form with the file metadata received from API
        // *****
        // NB: We have nothing to write to the answers as the attachments 
        // are in a separate model with different API endpoints.
        // field.onChange(file);
    }, [field]);

    // Build the accept map expected by react-dropzone from the configured
    // mime types. react-dropzone accepts an object like { "image/png": [] }
    // where the array can contain file extensions; we don't need extensions
    // so we provide empty arrays.
    const clientConfig = ConfigManager.get();
    const acceptedTypes: Record<string, string[]> = (clientConfig.upload_mime_types ?? [])
        .reduce((acc: Record<string, string[]>, mime: string) => {
            if (mime && typeof mime === 'string') acc[mime] = [];
            return acc;
        }, {} as Record<string, string[]>);
    // console.log("Accepted mime types:", acceptedTypes);

    const {
        getInputProps,
        getRootProps,
        open: openFileDialog,
        isDragAccept,
        isDragReject,
    } = useDropzone({
        validator: fileSizeValidator,
        onDrop,
        onDragLeave: () => Reset(0),
        onDropRejected: () => Reset(3),
        accept: acceptedTypes,
        multiple: false,
        noClick: true,
        noKeyboard: true,
        noDragEventsBubbling: true,
    });

    const styling: IDragStateStyling = React.useMemo(
        () => getStyling(isDragAccept, isDragReject),
        [isDragAccept, isDragReject],
    );

    // Disable all drag n drop and click events while uploading 
    // to prevent user from interrupting the upload process
    const disabledHandlers = progress !== null ? {
        onClick: (e: any) => e.preventDefault(),
        onKeyDown: (e: any) => e.preventDefault(),
        onDrop: (e: any) => e.preventDefault(),
        onDragEnter: (e: any) => e.preventDefault(),
        onDragLeave: (e: any) => e.preventDefault(),
        onDragOver: (e: any) => e.preventDefault(),
    } : {};

    // Dropzone and file input props
    const inputProps = getInputProps();
    const rootProps = getRootProps({
        className: 'dropzone w-full flex flex-col gap-6 py-4 px-8 mt-4 ' +
            'items-center text-center border-2 border-dashed rounded-md ' +
            styling.borderColour,
        ...disabledHandlers,
    }) as React.HTMLAttributes<HTMLDivElement>;

    // console.log("inputProps:", inputProps)
    // console.log("rootProps:", rootProps)

    return (
        <Box {...rootProps}>
            <VisuallyHiddenInput {...inputProps} />
            {progress === null ?
                styling.icon :
                <LinearProgress variant="determinate" value={progress} color="success" className="w-full mt-8" />
            }

            {filename ? (
                <Typography color="textSecondary" variant="h6">
                    Uploading "{filename}"...
                </Typography>
            ) : (
                <>
                    <Typography color="textSecondary" variant="h6">
                        Drag and drop your file here or <br />
                        {/* Explicit upload button to open file selector */}
                        <Button
                            variant="outlined"
                            startIcon={<DriveFolderUploadIcon />}
                            onClick={openFileDialog}
                        >
                            Select from computer
                        </Button>
                    </Typography>
                    <Typography color={styling.textColour} fontStyle="italic">
                        Only images and PDF files are accepted.<br />
                        Maximum file size limit is 10MB.
                    </Typography>
                </>
            )}
        </Box>
    );
};


const fileSizeValidator = (file: File) => {
    const clientConfig = ConfigManager.get();

    if (typeof file.size === "undefined" || file.size <= clientConfig.upload_max_size)
        return null;

    // console.log("Max size:", clientConfig.upload_max_size)
    // console.log("File size:", file.size)
    // console.log("Bigger:", file.size > clientConfig.upload_max_size)

    return {
        code: "file-too-large",
        message: "File is too large.",
    };
}


interface IDragStateStyling {
    icon: React.ReactElement;
    borderColour: string;
    textColour: string;
}


/**
 * Decides what styling to apply based on the dropzone state.
 * 
 * @param isDragAccept Active drag over file will be accepted
 * @param isDragReject Dragged file (whether drag over or dropped) is rejected
 */
const getStyling = (isDragAccept: boolean, isDragReject: boolean): IDragStateStyling => {
    if (isDragAccept) {
        return {
            textColour: "success",
            borderColour: "border-green-500",
            icon: <CloudUploadIcon style={{ fontSize: 128 }} color="success" />
        }
    }

    if (isDragReject) {
        return {
            textColour: "error",
            borderColour: "border-red-500",
            icon: <BlockIcon style={{ fontSize: 128 }} color="error" />
        }
    }

    // The default state
    return {
        textColour: "textSecondary",
        borderColour: "border-gray-400",
        icon: <CloudUploadIcon style={{ fontSize: 128 }} color="action" />
    };
}
