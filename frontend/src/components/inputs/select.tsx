import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import FormControl from "@mui/material/FormControl";
import FormHelperText from "@mui/material/FormHelperText";
import MenuItem from "@mui/material/MenuItem";
import Select from "@mui/material/Select";
import Typography from "@mui/material/Typography";

import { Controller } from "react-hook-form";
import { ERROR_MSG } from "../../context/Constants";
import { Question } from "../../context/types/Questionnaire";
import { HintButton } from "../Common";

export function SelectInput({
    question,
}: {
    question: Readonly<Question>
}) {
    return <Controller
        name={question.key}
        defaultValue=""
        rules={{
            required: question.o.is_required ? ERROR_MSG.required : false,
        }}
        render={({ field, fieldState }) => (
            <FormControl fullWidth>
                <Box className="flex items-baseline-last gap-1">
                    <Typography variant="h6" component="label">
                        {question.labelText}
                    </Typography>
                    {question.o.config?.hint && (
                        <HintButton hint={question.o.config.hint} />
                    )}
                </Box>
                <Select
                    {...field}
                    value={field.value ?? ""}
                    error={fieldState.invalid}
                    inputProps={{
                        "aria-labelledby": "label-" + question.key,
                    }}
                >
                    {question.o.config?.select_options?.map((option) => (
                        <MenuItem key={option} value={option}>
                            {option}
                        </MenuItem>
                    ))}
                </Select>
                {fieldState.invalid &&
                    <Alert severity="error" sx={{ mt: 1 }}>
                        {fieldState.error?.message}
                    </Alert>
                }
                {question.o.description &&
                    <FormHelperText>
                        {question.o.description}
                    </FormHelperText>
                }
            </FormControl>
        )}
    />;
}