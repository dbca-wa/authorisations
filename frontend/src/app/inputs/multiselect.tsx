import { Question } from "@/app/data/FormData";
import { MenuItem } from "@mui/material";
import Select from "@mui/material/Select";

export function MultiSelectInput(question: Readonly<Question>) {
    return (
        <Select>
            {question.options?.map((option) => {
                return (
                    <MenuItem>
                        {option}
                    </MenuItem>
                )
            })}
        </Select>
    );
}