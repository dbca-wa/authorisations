import BlockIcon from '@mui/icons-material/Block';
import CancelOutlinedIcon from '@mui/icons-material/CancelOutlined';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import FormHelperText from "@mui/material/FormHelperText";
import LinearProgress from '@mui/material/LinearProgress';
import Typography from '@mui/material/Typography';
import type { AxiosError, AxiosProgressEvent } from 'axios';
import React from 'react';

import type { AlertColor } from '@mui/material/Alert';
import { useDropzone } from 'react-dropzone';
import { Controller, type ControllerRenderProps, type FieldValues } from "react-hook-form";
import { ApiManager } from '../../context/ApiManager';
import { ConfigManager } from '../../context/ConfigManager';
import { ERROR_MSG } from "../../context/Constants";
import { useDialog } from '../../context/Dialogs';
import { useSnackbar } from '../../context/Snackbar';
import type { Question } from "../../context/types/Questionnaire";
import { VisuallyHiddenInput } from '../../context/Utils';


export const FileInput = ({
    question,
    applicationKey,
}: {
    question: Readonly<Question>;
    applicationKey: string;
}) => {
    // Abort controlller to allow cancelling
    const controller = new AbortController();

    // Dropzone dialog for drag n drop
    const { showDialog, hideDialog } = useDialog();

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
                    <Button
                        component="label"
                        role={undefined}
                        variant="contained"
                        tabIndex={-1}
                        startIcon={<CloudUploadIcon />}
                        onClick={() => {
                            showDialog({
                                title: "Upload a file",
                                content: <DropzoneDialogContent
                                    applicationKey={applicationKey}
                                    field={field}
                                    signal={controller.signal}
                                    showSnackbar={showSnackbar}
                                />,
                                actions: (
                                    <Button
                                        variant="outlined"
                                        startIcon={<CancelOutlinedIcon />}
                                        onClick={() => {
                                            controller.abort();
                                            hideDialog();
                                        }}
                                    >
                                        Cancel
                                    </Button>
                                ),
                                onClose: () => controller.abort(),
                            });
                        }}
                    >
                        Upload
                    </Button>
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
}: {
    applicationKey: string;
    field: ControllerRenderProps<FieldValues, string>;
    signal: AbortSignal;
    showSnackbar: (message: React.ReactNode, severity?: AlertColor) => void;
}) => {
    // The name of the file being uploaded
    const [filename, setFilename] = React.useState<string | null>(null);
    // Uploading progress state (0-100) or null (not uploading yet)
    const [progress, setProgress] = React.useState<number | null>(null);

    // All the file drag state and logic is INSIDE the component
    // that will be rendered within the dialog.
    const onDrop = React.useCallback(async (acceptedFiles: File[], fileRejections: any[]) => {
        // We want exactly one file
        if (acceptedFiles.length !== 1 || fileRejections.length !== 0) return;

        const file = acceptedFiles[0];
        setFilename(file.name);
        // console.log("File selected:", file);

        // Start uploading the file via API
        const response = await ApiManager.uploadAttachment({
            key: applicationKey,
            field: field.name,
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
                return resp;
            })
            // Display the error message to user and log to console
            .catch((error: AxiosError) => {
                console.error('API Error:', error);
                const message = (error.response?.data as any)?.document?.[0] ?? error.message;
                showSnackbar(`Failed to upload: ${message}`, "error");
                return null;
            });

        // Something went wrong with the upload
        if (!response) return;

        // Update react-hook-form with the file metadata received from API
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
        isDragActive,
        isFocused,
        isDragAccept,
        isDragReject,
    } = useDropzone({
        onDrop,
        multiple: false,
        validator: fileSizeValidator,
        accept: acceptedTypes,
    });

    const styling: IDragStateStyling = React.useMemo(
        () => getStyling(isDragActive, isFocused, isDragAccept, isDragReject),
        [isDragActive, isFocused, isDragAccept, isDragReject],
    );

    // Dropzone and file input props
    const inputProps = getInputProps();
    const rootProps = getRootProps({
        className: `dropzone w-full py-32 px-30 border-2 border-dashed rounded-lg text-center ${styling.borderColour}`,
    }) as React.HTMLAttributes<HTMLDivElement>;

    // console.log("inputProps:", inputProps)
    // console.log("rootProps:", rootProps)

    // Upload has started
    if (progress !== null) {
        // Progress bar
        styling.icon = <LinearProgress variant="determinate" value={progress} color="success" />

        // Disable drag n drop and click events while uploading
        rootProps.onClick = (e) => e.preventDefault();
        rootProps.onKeyDown = (e) => e.preventDefault();
        rootProps.onDrop = (e) => e.preventDefault();
        rootProps.onDragEnter = (e) => e.preventDefault();
        rootProps.onDragLeave = (e) => e.preventDefault();
        rootProps.onDragOver = (e) => e.preventDefault();
    }

    return (
        <Box {...rootProps}>
            <VisuallyHiddenInput {...inputProps} />
            {styling.icon}
            <br /><br />

            {filename ? (
                <Typography color="textSecondary" variant="h6">
                    Uploading "{filename}"...
                </Typography>
            ) : (
                <>
                    <Typography color="textSecondary" variant="h6">
                        Drag and drop your file here <br />
                        (or click to select from computer)
                    </Typography><br />
                    <Typography color={styling.textColour} fontStyle="italic">
                        (Only images and PDF files are accepted. <br />
                        Maximum file size limit is 10MB.)
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
 * @param isDragActive The dropzone is being dragged over
 * @param isFocused The dropzone is focused via tab or mouse down
 * @param isDragAccept Dragged file is accepted
 * @param isDragReject Dragged file is rejected
 */
const getStyling = (
    isDragActive: boolean, isFocused: boolean,
    isDragAccept: boolean, isDragReject: boolean,
): IDragStateStyling => {
    const defaultStyling = {
        textColour: "textSecondary",
        borderColour: "border-gray-400",
        icon: <CloudUploadIcon style={{ fontSize: 128 }} color="action" />
    }

    if (isFocused && !isDragActive) {
        return {
            textColour: "textSecondary",
            borderColour: "border-blue-400",
            icon: <CloudUploadIcon style={{ fontSize: 128 }} color="info" />
        }
    }

    // if (!isDragActive) return defaultStyling;

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

    // Shouldn't get here but just in case
    // throw new Error("Unexpected state in getStyling");
    return defaultStyling;
}
