import dayjs from 'dayjs';

import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import FormHelperText from '@mui/material/FormHelperText';
import Typography from '@mui/material/Typography';

import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { Controller } from 'react-hook-form';
import { ERROR_MSG } from '../../context/Constants';
import { Question } from "../../context/types/Questionnaire";
import { HintButton } from "../Common";

export function DateInput({
    question,
}: {
    question: Readonly<Question>
}) {
    return <Controller
        name={question.key}
        defaultValue={null}
        rules={{
            required: question.o.is_required ? ERROR_MSG.required : false,
        }}
        render={({ field, fieldState }) => (
            <Box className="w-full">
                <Typography variant="h6" component="label" htmlFor={"field-" + question.key}>
                    {question.labelText}
                    {question.o.config?.hint && <HintButton hint={question.o.config.hint} />}
                </Typography>
                <DatePicker
                    value={field.value ? dayjs(field.value) : null}

                    // Convert to "YYYY-MM-DD" string or null
                    onChange={
                        (value) => field.onChange(value ? value.format('YYYY-MM-DD') : null)
                    }
                    slotProps={{
                        textField: {
                            id: "field-" + question.key,
                            error: fieldState.invalid,
                            fullWidth: true,
                        }
                    }}
                />
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
            </Box>
        )}
    />
}