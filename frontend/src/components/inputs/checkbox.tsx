import Checkbox from "@mui/material/Checkbox";
import FormControl from "@mui/material/FormControl";
import FormControlLabel from "@mui/material/FormControlLabel";
import FormHelperText from "@mui/material/FormHelperText";
import { Controller } from "react-hook-form";
import { Question } from "../../context/types/Questionnaire";
import { ERROR_MSG } from "../../context/Constants";

export function CheckboxInput({
    question,
}: {
    question: Readonly<Question>
}) {
    return <Controller
        name={question.key}
        defaultValue={false}
        rules={{
            required: question.o.is_required ? ERROR_MSG.required : false,
        }}
        render={({ field, fieldState }) => (
            <FormControl>
                <FormControlLabel
                    control={
                        <Checkbox
                            {...field}
                            checked={!!field.value}
                        />
                    }
                    label={question.labelText}
                />
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
    />
}
