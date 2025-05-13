import Checkbox from "@mui/material/Checkbox";
import FormControlLabel from "@mui/material/FormControlLabel";
import { Question } from "@/app/data/FormData";

export function CheckboxInput({
    question,
}: {
    question: Readonly<Question>
}) {
    return <FormControlLabel
        control={<Checkbox />}
        label={question.label}
        required={question.isRequired}
        className="w-full"
    />
}