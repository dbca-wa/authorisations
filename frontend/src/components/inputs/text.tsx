import TextField from "@mui/material/TextField";
import type { Question } from "../../context/FormTypes";


export function TextInput({
    question,
} : {
    question: Readonly<Question>,
}) {
    return <TextField
        label={question.labelText}
        defaultValue={question.value}
        helperText={question.o.description}
        required={question.o.is_required}
        variant="outlined"
        className="w-full"
    />
}