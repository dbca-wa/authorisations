import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Checkbox from "@mui/material/Checkbox";
import FormControl from "@mui/material/FormControl";
import FormControlLabel from "@mui/material/FormControlLabel";
import FormHelperText from "@mui/material/FormHelperText";
import Typography from "@mui/material/Typography";

import { Controller } from "react-hook-form";
import { Question } from "../../context/types/Questionnaire";
import { ERROR_MSG } from "../../context/Constants";
import { HintButton } from "../Common";

export function CheckboxInput({
    question,
}: {
    question: Readonly<Question>
}) {
    return <Controller
        name={question.key}
        defaultValue={false}
        rules={{
            required: question.o.is_required ? ERROR_MSG.required : false,
        }}
        render={({ field, fieldState }) => (
            <FormControl>
                <Box className="flex items-start gap-1">
                    <Typography variant="h6">
                        {question.number}
                    </Typography>
                    <FormControlLabel
                        control={
                            <Checkbox
                                {...field}
                                checked={!!field.value}
                                className="pt-1!"
                            />
                        }
                        label={
                            <Typography variant="h6">
                                {question.o.label}
                                {question.o.is_required && " *"}
                                {question.o.config?.hint && <HintButton hint={question.o.config.hint} />}
                            </Typography>
                        }
                        className="m-0! items-start!"
                    />
                </Box>
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
    />
}
