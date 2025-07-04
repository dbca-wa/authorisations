import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import dayjs from 'dayjs';
import { Controller } from 'react-hook-form';
import { Question } from '../../context/FormTypes';
import { ERROR_MSG } from './errors';

export function DateInput({
    question,
}: {
    question: Readonly<Question>
}) {
    return <Controller
        name={question.id}
        defaultValue={
            question.value && (typeof question.value === 'string')
                ? dayjs(question.value)
                : null
        }
        rules={{
            required: question.o.is_required ? ERROR_MSG.required : false,
        }}
        render={({ field, fieldState }) => (
            <DatePicker
                {...field}
                label={question.labelText}
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