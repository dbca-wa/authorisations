import Alert from "@mui/material/Alert";
import FormControl from "@mui/material/FormControl";
import FormHelperText from "@mui/material/FormHelperText";
import MenuItem from "@mui/material/MenuItem";
import Select from "@mui/material/Select";

import { Controller } from "react-hook-form";
import { ERROR_MSG } from "../../context/Constants";
import { Question } from "../../context/types/Questionnaire";

export function SelectInput({
    question,
}: {
    question: Readonly<Question>
}) {
    return <Controller
        name={question.key}
        defaultValue=""
        rules={{
            required: question.o.is_required ? ERROR_MSG.required : false,
        }}
        render={({ field, fieldState }) => (
            <FormControl fullWidth>
                <label
                    id={"label-" + question.key}
                    htmlFor={"field-" + question.key}
                    className="mb-2 block whitespace-normal text-base leading-relaxed text-gray-800"
                >
                    {question.labelText}
                </label>
                <Select
                    {...field}
                    id={"field-" + question.key}
                    value={field.value ?? ""}
                    error={fieldState.invalid}
                    inputProps={{
                        "aria-labelledby": "label-" + question.key,
                    }}
                >
                    {question.o.config?.select_options?.map((option) => (
                        <MenuItem key={option} value={option}>
                            {option}
                        </MenuItem>
                    ))}
                </Select>
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
            </FormControl>
        )}
    />;
}