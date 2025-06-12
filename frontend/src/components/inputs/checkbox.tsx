import Checkbox from "@mui/material/Checkbox";
import FormControl from "@mui/material/FormControl";
import FormControlLabel from "@mui/material/FormControlLabel";
import FormHelperText from "@mui/material/FormHelperText";
import type { Question } from "../../context/FormTypes";

export function CheckboxInput({
    question,
}: {
    question: Readonly<Question>
}) {
    return (
        <FormControl>
            <FormControlLabel
                control={<Checkbox />}
                label={question.label}
                required={question.is_required}
                className="w-full"
            />
            {question.description && <FormHelperText>{question.description}</FormHelperText>}
        </FormControl>
    );
}