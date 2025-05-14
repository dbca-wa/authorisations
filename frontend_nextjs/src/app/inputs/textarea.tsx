import { Question } from "../data/FormData";
import TextField from "@mui/material/TextField";

export function TextAreaInput({
    question,
} : {
    question: Readonly<Question>
}) {
    return <TextField
        label={question.label}
        defaultValue={question.value}
        helperText={question.description}
        required={question.isRequired}
        variant="outlined"
        className="w-full"
        // Textarea specific props
        multiline
        minRows={3}
        maxRows={6}
    />
}