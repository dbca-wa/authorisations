import Box from "@mui/material/Box";
import FormHelperText from "@mui/material/FormHelperText";
import TextField from "@mui/material/TextField";
import { Controller } from "react-hook-form";
import { Question } from "../../context/FormTypes";
import { ERROR_MSG } from "../../context/Constants";


export function TextInput({
    question,
}: {
    question: Readonly<Question>,
}) {

    return <Controller
        name={question.id}
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