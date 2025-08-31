import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import dayjs from 'dayjs';
import { Controller } from 'react-hook-form';
import { ERROR_MSG } from '../../context/Constants';
import { Question } from "../../context/types/Questionnaire";

export function DateInput({
    question,
}: {
    question: Readonly<Question>
}) {
    return <Controller
        name={question.key}
        rules={{
            required: question.o.is_required ? ERROR_MSG.required : false,
        }}
        render={({ field, fieldState }) => (
            <DatePicker
                {...field}
                label={question.labelText}
                value={field.value ? dayjs(field.value) : null}
                // Convert to "YYYY-MM-DD" string or null
                onChange={
                    (value) => field.onChange(value ? value.format('YYYY-MM-DD') : null)
                }
                slotProps={{
                    textField: {
                        error: fieldState.invalid,
                        helperText: fieldState.error?.message || question.o.description,
                    }
                }}
            />
        )}
    />
}