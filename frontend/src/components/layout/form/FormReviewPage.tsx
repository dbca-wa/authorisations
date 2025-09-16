import EditIcon from '@mui/icons-material/Edit';
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Checkbox from '@mui/material/Checkbox';
import FormControl from '@mui/material/FormControl';
import FormControlLabel from '@mui/material/FormControlLabel';
import IconButton from "@mui/material/IconButton";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import Typography from "@mui/material/Typography";
import dayjs from "dayjs";
import React from "react";

import { grey } from "@mui/material/colors";
import { useFormContext } from "react-hook-form";
import type { IAnswer, IFormAnswers, IGridAnswerRow } from "../../../context/types/Application";
import type { AsyncVoidAction } from "../../../context/types/Generic";
import type { IGridQuestionColumn, IQuestion, IQuestionnaire } from "../../../context/types/Questionnaire";


// Dummy submit handler for now
const onSubmit = () => {

    alert("Submitted! (implement server-side integration here)");
};

export function FormReviewPage({
    questionnaire,
    handleSubmit,
}: {
    questionnaire: IQuestionnaire;
    handleSubmit: (nextStep: React.SetStateAction<number>) => AsyncVoidAction;
}) {
    const { getValues } = useFormContext<IFormAnswers>();
    const answers: IFormAnswers = getValues();

    const [hasConfirmed, setHasConfirmed] = React.useState<boolean>(false);

    return (
        <Box className="bg-gray-300 p-8 min-w-3xl max-w-7xl">
            <Typography variant="h4" gutterBottom>
                Review your answers
            </Typography>
            <Typography variant="subtitle1" gutterBottom color="text.secondary">
                Please review your answers below. You can go back to make changes if needed.
            </Typography>
            <Stack spacing={4} mt={2}>
                {questionnaire.steps.map((step: any, stepIdx: number) => (
                    <Paper elevation={3} key={stepIdx} sx={{ p: 3 }}>
                        <Typography variant="h5" gutterBottom>
                            {step.title}
                            <IconButton
                                size="small" color="primary" aria-label="edit step"
                                onClick={handleSubmit(stepIdx)}
                            >
                                <EditIcon />
                            </IconButton>
                        </Typography>
                        <Stack spacing={3}>
                            {step.sections.map((section: any, sectionIdx: number) => (
                                <Box key={sectionIdx}>
                                    <Typography variant="h6" sx={{ mb: 1 }}>
                                        {section.title}
                                    </Typography>
                                    <Stack spacing={2}>
                                        {section.questions.map((question: IQuestion, questionIdx: number) => {
                                            const answer = answers[stepIdx][`${sectionIdx}-${questionIdx}`];
                                            let displayAnswer: React.ReactNode = null;

                                            switch (question.type) {
                                                case "checkbox":
                                                    displayAnswer = displayCheckbox(answer);
                                                    break;
                                                case "grid":
                                                    displayAnswer = displayGrid(question, answer);
                                                    break;
                                                case "date":
                                                    displayAnswer = displayDate(answer);
                                                    break;
                                                case "select":
                                                case "number":
                                                case "textarea":
                                                case "text":
                                                    displayAnswer = displayString(answer);
                                                    break;
                                                default:
                                                    throw new Error(`Unsupported question type: ${question.type}`);
                                            }

                                            return (
                                                <Box key={questionIdx} sx={{ mb: 1 }}>
                                                    <Typography variant="subtitle1" sx={{ fontWeight: 500 }}>
                                                        {question.label}
                                                    </Typography>
                                                    {displayAnswer}
                                                </Box>
                                            );
                                        })}
                                    </Stack>
                                </Box>
                            ))}
                        </Stack>
                    </Paper>
                ))}
            </Stack>
            <Box justifyContent="space-around" display="flex" mt={4}>
                <FormControl>
                    <FormControlLabel
                        control={<Checkbox checked={hasConfirmed} />}
                        onChange={(_event, checked) => setHasConfirmed(checked)}
                        label="I confirm that the information provided in this application is accurate and complete."
                    />
                </FormControl>
            </Box>
            <Box justifyContent="space-around" display="flex">
                <Button
                    variant="contained" size="large" color="success"
                    onClick={onSubmit}
                    disabled={!hasConfirmed}
                >
                    Submit Application
                </Button>
            </Box>
        </Box>
    );
}



const humaniseBoolean = (val: IAnswer): string => {
    if (val === true) return "Yes";
    if (val === false) return "No";
    return "N/A";
}

const isEmptyAnswer = (answer: any) => {
    return (
        // answer === undefined ||
        answer === null ||
        (typeof answer === "string" && answer.trim() === "") ||
        (Array.isArray(answer) && answer.length === 0)
    );
}

const displayCheckbox = (answer: IAnswer) => (
    <Typography sx={{ fontWeight: "bold" }}>
        {humaniseBoolean(answer)}
    </Typography>
);

const displayGrid = (question: IQuestion, answer: IAnswer) => {
    if (!Array.isArray(answer)) {
        return <Typography sx={{ color: grey[500] }}>N/A</Typography>;
    }
    if (answer.length === 0) {
        return <Typography sx={{ color: grey[500] }}>(unanswered)</Typography>;
    }
    return (
        <TableContainer component={Paper} variant="outlined" sx={{ maxWidth: "100%", mb: 1 }}>
            <Table size="small">
                <TableHead>
                    <TableRow>
                        {question.grid_columns?.map((col: IGridQuestionColumn, colIdx: number) => (
                            <TableCell key={colIdx}>{col.label}</TableCell>
                        ))}
                    </TableRow>
                </TableHead>
                <TableBody>
                    {answer.map((row: IGridAnswerRow, rowIdx: number) => (
                        <TableRow key={rowIdx}>
                            {question.grid_columns?.map((col: IGridQuestionColumn, colIdx: number) => {
                                const cellValue = row[col.label];
                                let displayValue: React.ReactNode;

                                if (col.type === "checkbox") {
                                    displayValue = humaniseBoolean(cellValue);
                                } else if (col.type === "date") {
                                    displayValue = displayDate(cellValue);
                                } else if (cellValue === null || cellValue === undefined || (typeof cellValue === "string" && cellValue.trim() === "")) {
                                    displayValue = <Typography sx={{ color: grey[500] }}>(unanswered)</Typography>;
                                } else {
                                    displayValue = String(cellValue);
                                }

                                return <TableCell key={colIdx} sx={{ fontWeight: "bold" }}>{displayValue}</TableCell>;
                            })}
                        </TableRow>
                    ))}
                </TableBody>
            </Table>
        </TableContainer>
    );
};

const displayDate = (answer: IAnswer) => {
    return isEmptyAnswer(answer)
        ? <Typography sx={{ color: grey[500] }}>(unanswered)</Typography>
        : <Typography sx={{ fontWeight: "bold" }}>{dayjs(answer as string).format('DD/MM/YYYY')}</Typography>;
};

const displayString = (answer: IAnswer) => {
    return isEmptyAnswer(answer)
        ? <Typography sx={{ color: grey[500] }}>(unanswered)</Typography>
        : <Typography sx={{ fontWeight: "bold" }}>{String(answer)}</Typography>;
};