import TextField from "@mui/material/TextField";
import { Question } from "../data/FormData";


export function TextInput(question : Readonly<Question>) {
    return <TextField
        label={question.label}
        // defaultValue="Default Value"
        helperText={question.description}
        required={question.isRequired}
        variant="outlined"
        className="w-full"
    />
}