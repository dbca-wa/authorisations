import TextField from "@mui/material/TextField";
import type { Question } from "../../context/FormTypes";


export function TextInput({
    question,
} : {
    question: Readonly<Question>
}) {
    return <TextField
        label={question.label}
        defaultValue={question.value}
        helperText={question.description}
        required={question.is_required}
        variant="outlined"
        className="w-full"
    />
}