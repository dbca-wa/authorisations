import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { Question } from "../data/FormData";
import dayjs from 'dayjs';

export function DateInput({
    question,
}: {
    question: Readonly<Question>
}) {
    return <DatePicker
        label={question.label}
        value={
            question.value && (typeof question.value === 'string')
                ? dayjs(question.value)
                : null
        }
    />
}