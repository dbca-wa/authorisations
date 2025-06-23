import TextField from "@mui/material/TextField";
import type { Question } from "../../context/FormTypes";

export function TextAreaInput({
    question,
} : {
    question: Readonly<Question>
}) {
    return <TextField
        label={question.indexText + question.label}
        defaultValue={question.value}
        helperText={question.description}
        required={question.is_required}
        variant="outlined"
        className="w-full"
        // Textarea specific props
        multiline
        minRows={3}
        maxRows={6}
    />
}