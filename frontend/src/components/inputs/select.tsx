import { FormControl, FormHelperText, InputLabel, MenuItem } from "@mui/material";
import Select from "@mui/material/Select";
import { Controller } from "react-hook-form";
import { Question } from "../../context/FormTypes";
import { ERROR_MSG } from "../../context/Constants";

export function SelectInput({
    question,
}: {
    question: Readonly<Question>
}) {
    return <Controller
        name={question.id}
        rules={{
            required: question.o.is_required ? ERROR_MSG.required : false,
        }}
        render={({ field, fieldState }) => (
            // Use error attribute on children only, not on FormControl 
            // so the description helper text will always display normal
            <FormControl fullWidth>
                <InputLabel
                    id={"label-" + question.id}
                    error={fieldState.invalid}
                >
                    {question.labelText}
                </InputLabel>
                <Select
                    {...field}
                    label={question.labelText}
                    labelId={"label-" + question.id}
                    error={fieldState.invalid}
                >
                    {question.o.select_options?.map((option) => (
                        <MenuItem key={option} value={option}>
                            {option}
                        </MenuItem>
                    ))}
                </Select>
                {fieldState.invalid &&
                    <FormHelperText error>
                        {fieldState.error?.message}
                    </FormHelperText>
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