import BlockIcon from '@mui/icons-material/Block';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import FormHelperText from "@mui/material/FormHelperText";
import Typography from '@mui/material/Typography';
import React from 'react';
import { useDropzone } from 'react-dropzone';
import { Controller, type ControllerRenderProps, type FieldValues } from "react-hook-form";
import { ERROR_MSG } from "../../context/Constants";
import { useDialog } from '../../context/Dialogs';
import type { Question } from "../../context/types/Questionnaire";
import { VisuallyHiddenInput } from '../../context/Utils';


export const FileInput = ({
    question,
}: {
    question: Readonly<Question>,
}) => {
    const { showDialog, hideDialog } = useDialog();

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
                    <Button
                        component="label"
                        role={undefined}
                        variant="contained"
                        tabIndex={-1}
                        startIcon={<CloudUploadIcon />}
                        onClick={() => {
                            showDialog({
                                title: "Upload a file",
                                content: <DropzoneDialogContent field={field} />,
                                actions: <Button onClick={hideDialog}>Cancel</Button>,
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
    field,
}: {
    field: ControllerRenderProps<FieldValues, string>
}) => {
    // All the file drag state and logic is INSIDE the component
    // that will be rendered within the dialog.
    const onDrop = React.useCallback((acceptedFiles: File[]) => {
        // We want exactly one file
        if (acceptedFiles.length !== 1) return;
        const file = acceptedFiles[0];

        // Start uploading the file via API

        console.log("File selected:", file);
        // Update react-hook-form with the file object
        // field.onChange(file);

    }, [field]);

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
        accept: {
            "image/jpeg": [],
            "image/png": [],
            "application/pdf": [],
        }
    });

    const styling: IDragStateStyling = React.useMemo(
        () => getStyling(isDragActive, isFocused, isDragAccept, isDragReject),
        [isDragActive, isFocused, isDragAccept, isDragReject],
    );

    // `dropzone w-full py-32 px-24 border-2 border-dashed rounded-lg text-center ${borderColour}`
    const inputProps = getInputProps();
    const rootProps = getRootProps({
        className: `dropzone w-full py-32 px-30 border-2 border-dashed rounded-lg text-center ${styling.borderColour}`,
    }) as React.HTMLAttributes<HTMLDivElement>;

    // console.log("inputProps:", inputProps)
    // console.log("rootProps:", rootProps)

    return (
        <Box {...rootProps}>
            {styling.icon}<br /><br />
            <Typography color="textSecondary" variant="h6">
                Drag and drop some files here <br />
                (or click to select from computer)
            </Typography><br />
            <Typography color={styling.textColour} fontStyle="italic">
                (Only images and PDF files are accepted. <br />
                Maximum file size limit is 10MB.)
            </Typography>
            <VisuallyHiddenInput {...inputProps} />
        </Box>
    );
};


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

    if (!isDragActive) return defaultStyling;

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
    throw new Error("Unexpected state in getStyling");
    return defaultStyling;
}