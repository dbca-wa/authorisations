import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import FormHelperText from "@mui/material/FormHelperText";
import Typography from '@mui/material/Typography';
import { useDropzone } from 'react-dropzone';
import { Controller } from "react-hook-form";
import { ERROR_MSG } from "../../context/Constants";
import { useDialog } from '../../context/Dialogs';
import type { Question } from "../../context/types/Questionnaire";
import React from 'react';


export const getBorderColour = (isFocused: boolean, isDragAccept: boolean, isDragReject: boolean) => {
    if (isDragAccept) {
        return "border-green-500"
    }

    if (isDragReject) {
        return "border-red-500"
    }

    if (isFocused) {
        return "border-blue-400";
    }

    // Default
    return "border-gray-400";
}

export const FileInput = ({
    question,
}: {
    question: Readonly<Question>,
}) => {

    const {
        getRootProps,
        getInputProps,
        isFocused,
        isDragAccept,
        isDragReject,
        acceptedFiles,
        fileRejections,
    } = useDropzone({
        multiple: false,
        accept: {
            'image/jpeg': [],
            'image/png': []
        }
    });

    const borderColour = React.useMemo(
        () => getBorderColour(isFocused, isDragAccept, isDragReject),
        [isFocused, isDragAccept, isDragReject],
    );
    
    // `dropzone w-full py-32 px-24 border-2 border-dashed rounded-lg text-center ${borderColour}`
    const dropZoneProps = getInputProps();
    const rootProps = getRootProps({
        className: `dropzone w-full py-32 px-24 border-2 border-dashed rounded-lg text-center ${borderColour}`,
    })

    // console.log("dropZoneProps:", dropZoneProps);
    // console.log("rootProps:", rootProps);

    const { showDialog, hideDialog } = useDialog();

    

    console.log("borderColour:", borderColour)

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
                <Box
                    className="w-full"
                // {...getRootProps({ className: "w-full dropzone" })}
                >
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
                                title: "Upload",
                                content: (
                                    <Box
                                        {...rootProps}
                                        // className={`dropzone w-full py-32 px-24 border-2 border-dashed rounded-lg text-center ${borderColour}`}
                                        // className={`dropzone w-full py-32 px-24 border-2 border-dashed rounded-lg text-center ${borderColour}`}
                                    >
                                        <Typography color="textSecondary" variant="h6">
                                            Drag and drop some files here <br />
                                            (or click to select from computer)
                                        </Typography><br />
                                        <Typography color="textSecondary" fontStyle="italic">
                                            (Only images and pdf files will be accepted)
                                        </Typography>
                                    </Box>
                                ),
                                actions: (
                                    <>
                                        <Button onClick={() => {
                                            hideDialog();
                                            // setInProgress("");
                                        }}>Cancel</Button>
                                        <Button onClick={async () => {
                                            console.log("Confirmed!");
                                            // await createNewApplication(questionnaire.slug, navigate);
                                        }}>
                                            Confirm
                                        </Button>
                                    </>
                                )
                            });
                        }}
                    >
                        Upload
                        {/* <VisuallyHiddenInput
                            type="file"
                            {...dropZoneProps}
                            {...field}
                            onChange={(event: React.ChangeEvent<HTMLInputElement>) => {
                                field.onChange(event); // react-hook-form integration
                                dropZoneProps.onChange?.(event); // react-dropzone integration
                                console.log(event.target.files)
                            }}
                        /> */}
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


