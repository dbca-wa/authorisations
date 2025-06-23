import { FormControl, InputLabel, MenuItem } from "@mui/material";
import Select from "@mui/material/Select";
import type { Question } from "../../context/FormTypes";

export function SelectInput({
    question,
}: {
    question: Readonly<Question>
}) {
    return (
        <FormControl fullWidth>
            <InputLabel >{question.indexText}{question.label}</InputLabel>
            <Select
                label={question.label}
                defaultValue={question.value || ''}
            >
                {question.select_options?.map((option) => {
                    return (
                        <MenuItem key={option} value={option}>
                            {option}
                        </MenuItem>
                    )
                })}
            </Select>
        </FormControl>
    );
}