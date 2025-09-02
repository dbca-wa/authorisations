import Box from "@mui/material/Box";
import FormHelperText from "@mui/material/FormHelperText";
import TextField from "@mui/material/TextField";
import { Controller } from "react-hook-form";
import { ERROR_MSG } from "../../context/Constants";
import { Question } from "../../context/types/Questionnaire";


export function TextInput({
    question,
}: {
    question: Readonly<Question>,
}) {

    return <Controller
        name={question.key}
        rules={{
            required: question.o.is_required ? ERROR_MSG.required : false,
        }}
        render={({ field, fieldState }) => (
            <Box className="w-full">
                <TextField
                    {...field}
                    label={question.labelText}
                    helperText={fieldState.invalid
                        ? fieldState.error?.message : question.o.description}
                    error={fieldState.invalid}
                    variant="outlined"
                    className="w-full"
                    
                    // Trim the value on blur for a better user experience.
                    // This allows users to type spaces between words and cleans up the
                    // value only when they are done editing.
                    onBlur={() => {
                        field.onBlur(); // First, call the original onBlur from react-hook-form
                        if (typeof field.value === 'string') {
                            field.onChange(field.value.trim()); // Then, update the value with the trimmed version
                        }
                    }}
                />
                {fieldState.invalid && question.o.description && (
                    <FormHelperText>
                        {question.o.description}
                    </FormHelperText>
                )}
            </Box>
        )}
    />
}