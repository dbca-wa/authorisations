import BlockIcon from '@mui/icons-material/Block';
import CancelOutlinedIcon from '@mui/icons-material/CancelOutlined';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import ComputerIcon from '@mui/icons-material/Computer';
import DriveFolderUploadIcon from '@mui/icons-material/DriveFolderUpload';
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
import type { IApplicationAttachment } from '../../context/types/Application';
import type { Question } from "../../context/types/Questionnaire";
import { VisuallyHiddenInput } from '../../context/Utils';
import { FileAttachmentList } from '../Common';

// Initially we start with allowing only 1 file per question to keep things simple.
// But later on, we may extend this functionality to allow multiple files with minor UI changes.
const MAX_FILES_PER_QUESTION = 3;

export const FileInput = ({
    question,
    attachments,
    applicationKey,
}: {
    question: Readonly<Question>;
    attachments: IApplicationAttachment[];
    applicationKey: string;
}) => {
    // Abort controlller to allow cancelling
    const controller = new AbortController();

    // Dropzone dialog for drag n drop
    // const { showDialog, hideDialog } = useDialog();

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
                    {attachments.length > 0 && FileAttachmentList({ attachments: attachments, canDelete: true })}
                    {/* Show the dropzone if we have less than the max allowed files for this question */}
                    {attachments.length < MAX_FILES_PER_QUESTION &&
                        <DropzoneDialogContent
                            applicationKey={applicationKey}
                            field={field}
                            signal={controller.signal}
                            showSnackbar={showSnackbar}
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
            appKey: applicationKey,
            name: file.name,
            answer: field.name,
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
                const responseData = error.response?.data as any;
                const message = responseData.document?.[0]
                    ?? responseData?.file?.[0]
                    ?? error.message;
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

    // Reference to the hidden input so we can trigger the file selector from a button
    const inputRef = React.useRef<HTMLInputElement | null>(null);

    const styling: IDragStateStyling = React.useMemo(
        () => getStyling(isDragActive, isFocused, isDragAccept, isDragReject),
        [isDragActive, isFocused, isDragAccept, isDragReject],
    );

    // Dropzone and file input props
    const inputProps = getInputProps();
    const rootProps = getRootProps({
        className: `dropzone w-full mt-4 py-8 px-8 border-2 border-dashed rounded-md text-center ${styling.borderColour}`,
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
            <VisuallyHiddenInput {...inputProps} ref={inputRef} />
            {styling.icon}
            <br />

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
                            onClick={() => inputRef.current?.click()}
                        >
                            Select from computer
                        </Button>
                    </Typography><br />
                    <Typography color={styling.textColour} fontStyle="italic">
                        Only images and PDF files are accepted. <br />
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
