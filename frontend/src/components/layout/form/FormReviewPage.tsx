import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import Typography from "@mui/material/Typography";
import { grey } from "@mui/material/colors";
import React from "react";
import { useFormContext } from "react-hook-form";
import type {
    IAnswer, IAnswers, IGridAnswerRow,
} from "../../../context/types/Application";
import type { IGridQuestionColumn, IQuestion, IQuestionnaire } from "../../../context/types/Questionnaire";

function humanizeBoolean(val: IAnswer): string {
    if (val === true) return "Yes";
    if (val === false) return "No";
    return "N/A";
}

function isEmptyAnswer(answer: any) {
    return (
        // answer === undefined ||
        answer === null ||
        (typeof answer === "string" && answer.trim() === "") ||
        (Array.isArray(answer) && answer.length === 0)
    );
}

function getAnswerKey(stepIdx: number, sectionIdx: number, questionIdx: number) {
    return `${stepIdx}-${sectionIdx}-${questionIdx}`;
}

// Dummy submit handler for now
const onSubmit = () => {
    alert("Submitted! (implement server-side integration here)");
};

export function FormReviewPage({
    questionnaire,
    onBack,
}: {
    questionnaire: IQuestionnaire;
    onBack: () => void;
}) {
    const { getValues } = useFormContext<IAnswers>();
    const answers: IAnswers = getValues();

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
                        </Typography>
                        <Stack spacing={3}>
                            {step.sections.map((section: any, sectionIdx: number) => (
                                <Box key={sectionIdx}>
                                    <Typography variant="h6" sx={{ mb: 1 }}>
                                        {section.title}
                                    </Typography>
                                    <Stack spacing={2}>
                                        {section.questions.map((question: IQuestion, questionIdx: number) => {
                                            const answerKey = getAnswerKey(stepIdx, sectionIdx, questionIdx);
                                            const answer = answers[answerKey];
                                            let displayAnswer: React.ReactNode = null;

                                            switch (question.type) {
                                                case "checkbox":
                                                    displayAnswer = (
                                                        <Typography sx={{ fontWeight: "bold" }}>
                                                            {humanizeBoolean(answer)}
                                                        </Typography>
                                                    );
                                                    break;
                                                case "grid":
                                                    if (Array.isArray(answer)) {
                                                        if (answer.length === 0) {
                                                            displayAnswer = (
                                                                <Typography sx={{ color: grey[500] }}>N/A</Typography>
                                                            );
                                                        } else {
                                                            displayAnswer = (
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

                                                                                        if (typeof cellValue === "boolean") {
                                                                                            displayValue = humanizeBoolean(cellValue);
                                                                                        } else if (cellValue === null || cellValue === undefined || (typeof cellValue === "string" && cellValue.trim() === "")) {
                                                                                            displayValue = <Typography sx={{ color: grey[500] }}>N/A</Typography>;
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
                                                        }
                                                    } else {
                                                        displayAnswer = (
                                                            <Typography sx={{ color: grey[500] }}>N/A</Typography>
                                                        );
                                                    }
                                                    break;
                                                case "select":
                                                case "date":
                                                case "number":
                                                    displayAnswer = isEmptyAnswer(answer)
                                                        ? <Typography sx={{ color: grey[500] }}>N/A</Typography>
                                                        : <Typography sx={{ fontWeight: "bold" }}>{String(answer)}</Typography>;
                                                    break;
                                                case "textarea":
                                                case "text":
                                                    displayAnswer = isEmptyAnswer(answer)
                                                        ? <Typography sx={{ color: grey[500] }}>N/A</Typography>
                                                        : <Typography sx={{ fontWeight: "bold" }}>{String(answer)}</Typography>;
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
                <Button variant="outlined" onClick={onBack}>
                    Back
                </Button>
                <Button variant="contained" color="primary" onClick={onSubmit}>
                    Submit
                </Button>
            </Box>
        </Box>
    );
}