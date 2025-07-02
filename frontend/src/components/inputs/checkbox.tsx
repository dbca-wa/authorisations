import Checkbox from "@mui/material/Checkbox";
import FormControl from "@mui/material/FormControl";
import FormControlLabel from "@mui/material/FormControlLabel";
import FormHelperText from "@mui/material/FormHelperText";
import type { Question } from "../../context/FormTypes";
import { useFormContext } from "react-hook-form";

export function CheckboxInput({
    question,
}: {
    question: Readonly<Question>
}) {
    const { register, formState: { errors } } = useFormContext()
    // console.log("Form state:", question.index, errors)
    // console.log("Question:", question)

    return (
        <FormControl>
            <FormControlLabel
                control={<Checkbox />}
                label={question.labelText}
                {...register(question.id, {
                    required: question.o.is_required ? "This field is required" : false,
                    // value: question.value ?? false,
                })}
            />
            {errors[question.id] &&
                <FormHelperText error>
                    {errors[question.id]?.message as string}
                </FormHelperText>
            }
            {question.o.description &&
                <FormHelperText>
                    {question.o.description}
                </FormHelperText>
            }
        </FormControl>
    );
}