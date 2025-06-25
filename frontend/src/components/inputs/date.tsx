import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import dayjs from 'dayjs';
import type { Question } from '../../context/FormTypes';

export function DateInput({
    question,
}: {
    question: Readonly<Question>
}) {
    return <DatePicker
        label={question.indexText + question.label}
        value={
            question.value && (typeof question.value === 'string')
                ? dayjs(question.value)
                : null
        }
    />
}