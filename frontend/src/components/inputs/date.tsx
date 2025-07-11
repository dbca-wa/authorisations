import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { Controller } from 'react-hook-form';
import { Question } from '../../context/FormTypes';
import { ERROR_MSG } from '../../context/Constants';
import dayjs from 'dayjs';

export function DateInput({
    question,
}: {
    question: Readonly<Question>
}) {
    return <Controller
        name={question.id}
        defaultValue={
            // Always pass the actual string value to the DatePicker
            question.value && typeof question.value === "string"
                ? question.value
                : null
        }
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