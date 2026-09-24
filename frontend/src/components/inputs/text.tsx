import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import FormHelperText from "@mui/material/FormHelperText";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";

import { Controller } from "react-hook-form";
import { ERROR_MSG } from "../../context/Constants";
import { Question } from "../../context/types/Questionnaire";
import { HintButton } from "../Common";


export function TextInput({
    question,
}: {
    question: Readonly<Question>,
}) {

    // Define textarea-specific props conditionally. If the type is not 'textarea',
    // this will be an empty object, and spreading it will do nothing.
    const textAreaProps = question.o.type === "textarea" ? {
        multiline: true,
        minRows: 3,
        maxRows: 20,
    } : {};

    return <Controller
        name={question.key}
        // React controlled vs uncontrolled warning fix:
        // This registers the field with an empty string if no
        // value is provided in the form's defaultValues. This ensures the
        // submitted data contains an empty string instead of undefined.
        defaultValue=""
        rules={{
            required: question.o.is_required ? ERROR_MSG.required : false,
        }}
        render={({ field, fieldState }) => (
            <Box className="w-full">
                <Typography variant="h6" component="label" htmlFor={"field-" + question.key}>
                    {question.labelText}
                    {question.o.config?.hint && <HintButton hint={question.o.config.hint} />}
                </Typography>
                <TextField
                    {...field}
                    id={"field-" + question.key}
                    type={question.o.type === "number" ? "number" : "text"}
                    error={fieldState.invalid}
                    variant="outlined"
                    fullWidth
                    // Trim the value on blur for a better user experience.
                    // This allows users to type spaces between words and cleans up the
                    // value only when they are done editing.
                    onBlur={() => {
                        field.onBlur();
                        if (typeof field.value === "string") {
                            field.onChange(field.value.trim());
                        }
                    }}
                    // Spread the conditional props here
                    {...textAreaProps}
                />
                {fieldState.invalid &&
                    <Alert severity="error" sx={{ mt: 1 }}>
                        {fieldState.error?.message}
                    </Alert>
                }
                {question.o.description &&
                    <FormHelperText>
                        {question.o.description}
                    </FormHelperText>
                }
            </Box>
        )}
    />
}