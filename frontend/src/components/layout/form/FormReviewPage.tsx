import AssignmentTurnedInRoundedIcon from '@mui/icons-material/AssignmentTurnedInRounded';
import EditIcon from '@mui/icons-material/Edit';
import Button from "@mui/material/Button";
import Checkbox from '@mui/material/Checkbox';
import FormControl from '@mui/material/FormControl';
import FormControlLabel from '@mui/material/FormControlLabel';
import IconButton from "@mui/material/IconButton";
import Typography from "@mui/material/Typography";
import dayjs from "dayjs";
import React from "react";

import type { AxiosError } from 'axios';
import { useFormContext } from "react-hook-form";
import { ApiManager } from '../../../context/ApiManager';
import { useSnackbar } from '../../../context/Hooks';
import { TurnstileManager } from '../../../context/TurnstileManager';
import { fireConfettiEffect } from '../../../context/confettiEffect';
import type { IAnswer, IApplicationAttachment, IFormAnswers, IGridAnswerRow } from "../../../context/types/Application";
import type { AsyncVoidAction } from "../../../context/types/Generic";
import { Question, type IFormSection, type IFormStep, type IGridQuestionColumn, type IQuestion, type IQuestionnaire } from "../../../context/types/Questionnaire";
import { FileAttachmentList } from '../../Common';

const getStepPrefix = (stepIndex: number) => `${stepIndex + 1}.`;
const getSectionPrefix = (sectionIndex: number) => `${String.fromCharCode(65 + sectionIndex)})`;


export function FormReviewPage({
    userCanEdit,
    setUserCanEdit,
    questionnaire,
    attachments,
    applicationKey,
    handleSubmit,
}: {
    userCanEdit: boolean,
    setUserCanEdit: React.Dispatch<React.SetStateAction<boolean>>;
    questionnaire: IQuestionnaire;
    attachments: IApplicationAttachment[];
    applicationKey: string;
    handleSubmit: (nextStep: React.SetStateAction<number>) => AsyncVoidAction;
}) {
    const { getValues } = useFormContext<IFormAnswers>();
    const answers: IFormAnswers = getValues();

    const [hasConfirmed, setHasConfirmed] = React.useState<boolean>(false);
    const [turnstileLoading, setTurnstileLoading] = React.useState<boolean>(userCanEdit);
    const [turnstileError, setTurnstileError] = React.useState<string | null>(null);
    const [turnstileToken, setTurnstileToken] = React.useState<string | null>(null);
    const hasInitializedRef = React.useRef<boolean>(false);
    const turnstileContainerRef = React.useRef<HTMLDivElement | null>(null);

    const { showSnackbar } = useSnackbar();

    /**
     * Render the Turnstile widget once and rely on callbacks to unlock
     * final confirmation only after successful verification.
     */
    React.useEffect(() => {
        // Read-only review mode does not need Turnstile verification.
        if (!userCanEdit) {
            return;
        }

        // Prevent duplicate initialisation in React StrictMode development.
        if (hasInitializedRef.current) {
            return;
        }
        hasInitializedRef.current = true;

        const initialiseTurnstile = async () => {
            try {
                setTurnstileLoading(true);
                setTurnstileError(null);
                setTurnstileToken(null);

                const container = turnstileContainerRef.current;
                if (!container) {
                    setTurnstileError("Verification widget container not found.");
                    setTurnstileLoading(false);
                    return;
                }

                await TurnstileManager.render(container, {
                    onSuccess: (token: string) => {
                        setTurnstileToken(token);
                        setTurnstileError(null);
                        setTurnstileLoading(false);
                    },
                    onError: () => {
                        setTurnstileToken(null);
                        setTurnstileError("Verification failed. Please try again.");
                        setTurnstileLoading(false);
                    },
                    onExpire: () => {
                        setTurnstileToken(null);
                        setTurnstileLoading(true);
                    },
                });
            } catch (error) {
                setTurnstileError(
                    error instanceof Error ? error.message : "Verification widget failed to initialise.",
                );
                setTurnstileLoading(false);
            }
        };

        initialiseTurnstile();
    }, [userCanEdit]);

    const isTurnstileVerified = !userCanEdit || (!turnstileLoading && !turnstileError && !!turnstileToken);

    // Dummy submit handler for now
    const onFinalSubmit = async () => {
        if (userCanEdit && !turnstileToken) {
            showSnackbar("Please complete verification before submitting.", "error");
            return;
        }

        // alert("Submitted! (implement server-side integration here)");
        await ApiManager.submitApplication(applicationKey, turnstileToken || "")
            // Successfully save to API    
            .then((resp) => {
                showSnackbar("Application has been successfully submitted and is read-only now.", "success");
                setUserCanEdit(false);
                fireConfettiEffect(5);
                return resp;
            })
            // Display the error message to user and log to console
            .catch((error: AxiosError) => {
                console.error('API Error:', error);
                const responseData = error.response?.data as {
                    turnstile_token?: string[];
                    status?: string[];
                } | undefined;
                const message = responseData?.turnstile_token?.[0] ?? responseData?.status?.[0] ?? error.message;
                showSnackbar(`Failed to submit: ${message}`, "error");
                return null;
            });

        // if (!response) return;
    };

    return (
        <div className="bg-gray-300 p-8 w-full lg:w-3xl xl:w-4xl 2xl:w-5xl">
            <p className="mb-2 text-3xl font-bold">
                Review your answers
            </p>
            <p className="mb-8 leading-6 text-[#4b5563]">
                Please review your answers below. You can go back to make changes if needed.
            </p>
            <div className="space-y-6">
                {questionnaire.steps.map((step: IFormStep, stepIdx: number) => (
                    <section key={stepIdx} className="overflow-hidden border border-[#222] bg-white">
                        <div className="flex items-center justify-between bg-[#2d5a8c] px-3 py-2">
                            <h2 className="m-0 text-base font-bold text-white">
                                {getStepPrefix(stepIdx)} {step.title}
                            </h2>
                            {userCanEdit &&
                                <IconButton
                                    size="small"
                                    aria-label="edit step"
                                    onClick={handleSubmit(stepIdx)}
                                    className="text-white! disabled:text-gray-300!"
                                >
                                    <EditIcon fontSize="small" />
                                </IconButton>
                            }
                        </div>

                        <div className="space-y-3 p-3">
                            {step.sections.map((section: IFormSection, sectionIdx: number) => (
                                <div key={sectionIdx} className="border border-[#222]">
                                    <div className="bg-[#e8f1f9] px-3 py-2">
                                        <h3 className="m-0 text-base font-bold text-[#111]">
                                            {getSectionPrefix(sectionIdx)} {section.title}
                                        </h3>
                                    </div>

                                    <div className="space-y-0">
                                        {section.questions.map((qObj: IQuestion, questionIdx: number) => {
                                            const question = new Question(qObj, {
                                                step: stepIdx,
                                                section: sectionIdx,
                                                question: questionIdx,
                                            });
                                            const answer = answers[stepIdx][`${sectionIdx}-${questionIdx}`];
                                            let displayAnswer: React.ReactNode;

                                            switch (qObj.type) {
                                                case "checkbox":
                                                    displayAnswer = displayCheckbox(answer);
                                                    break;
                                                case "grid":
                                                    displayAnswer = displayGrid(qObj, answer);
                                                    break;
                                                case "file":
                                                    displayAnswer = displayFiles(attachments.filter(atch => atch.question === question.key));
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
                                                    console.warn(`Unsupported question type: ${qObj.type}`);
                                                    displayAnswer = <Typography color="text.disabled">N/A - unsupported type</Typography>;
                                            }

                                            return (
                                                <div key={questionIdx} className="border-t border-[#222]">
                                                    <h4 className="m-0 bg-white px-3 py-2 text-[13px] font-bold text-[#173f82]">
                                                        {question.labelText}
                                                    </h4>
                                                    <div className="px-3 py-2 text-xs leading-[1.45]">{displayAnswer}</div>
                                                </div>
                                            );
                                        })}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </section>
                ))}
            </div>

            <div className="mt-8 flex justify-center">
                <FormControl>
                    {userCanEdit && (
                        <div className="mb-3 flex flex-col items-center">
                            <div ref={turnstileContainerRef} />
                            {turnstileError && (
                                <Typography variant="body2" color="error" sx={{ mt: 1, textAlign: "center" }}>
                                    Verification failed: {turnstileError}
                                </Typography>
                            )}
                        </div>
                    )}
                    <FormControlLabel
                        control={<Checkbox checked={hasConfirmed || !userCanEdit} />}
                        disabled={!userCanEdit || !isTurnstileVerified}
                        onChange={(_event, checked) => isTurnstileVerified && setHasConfirmed(checked)}
                        label="I confirm that the information provided in this application is accurate and complete."
                    />
                </FormControl>
            </div>

            <div className="flex justify-center">
                <Button
                    variant="contained"
                    size="large"
                    color="success"
                    onClick={onFinalSubmit}
                    disabled={!hasConfirmed || !userCanEdit || !isTurnstileVerified}
                    startIcon={<AssignmentTurnedInRoundedIcon />}
                >
                    Submit Application
                </Button>
            </div>
        </div>
    );
}



const humaniseBoolean = (val: IAnswer): string => {
    return val === true ? "Yes" : "No";
}

const isEmptyAnswer = (answer: IAnswer | undefined) => {
    return (
        // answer === undefined ||
        answer === null ||
        (typeof answer === "string" && answer.trim() === "") ||
        (Array.isArray(answer) && answer.length === 0)
    );
}

// Type guards to ensure answer is the correct type for each display function
const isCheckboxAnswer = (answer: IAnswer): answer is boolean => {
    return typeof answer === 'boolean';
};

const isGridAnswer = (answer: IAnswer): answer is IGridAnswerRow[] => {
    return Array.isArray(answer);
};

const isStringAnswer = (answer: IAnswer): answer is string => {
    return typeof answer === 'string';
};

const displayCheckbox = (answer: IAnswer) => {
    if (!isCheckboxAnswer(answer)) {
        console.warn(`Expected checkbox answer but got ${typeof answer}`, answer);
        return <Typography className="text-xs italic text-[#666]">N/A - invalid answer</Typography>;
    }
    return (
        <Typography component="span" className="text-sm font-medium text-[#111]">
            {humaniseBoolean(answer)}
        </Typography>
    );
};

const displayGrid = (question: IQuestion, answer: IAnswer) => {
    if (!isGridAnswer(answer)) {
        console.warn(`Expected grid answer but got ${typeof answer}`, answer);
        return <Typography className="text-xs italic text-[#666]">N/A - invalid answer</Typography>;
    }
    if (answer.length === 0) {
        return <Typography className="text-xs italic text-[#666]">(Not provided)</Typography>;
    }

    return (
        <div className="mb-1 overflow-x-auto">
            <table className="w-full border border-[#444] border-collapse text-[11px]">
                <thead>
                    <tr>
                        {question.grid_columns?.map((col: IGridQuestionColumn, colIdx: number) => (
                            <th key={colIdx} className="border border-[#777] bg-[#dbe4bf] px-2 py-1.5 text-left font-bold text-[#4f5f2f]">
                                {col.label}
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {answer.map((row: IGridAnswerRow, rowIdx: number) => (
                        <tr key={rowIdx}>
                            {question.grid_columns?.map((col: IGridQuestionColumn, colIdx: number) => {
                                const cellValue = row[col.label];
                                let displayValue: React.ReactNode;

                                if (col.type === "checkbox") {
                                    displayValue = humaniseBoolean(cellValue);
                                } else if (col.type === "date") {
                                    displayValue = displayDate(cellValue);
                                } else if (cellValue === null || cellValue === undefined || (typeof cellValue === "string" && cellValue.trim() === "")) {
                                    displayValue = <span className="italic text-[#666]">(Not provided)</span>;
                                } else {
                                    displayValue = String(cellValue);
                                }

                                return (
                                    <td key={colIdx} className="align-top border border-[#777] px-2 py-1.5 text-[#111]">
                                        {displayValue}
                                    </td>
                                );
                            })}
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};

const displayDate = (answer: IAnswer) => {
    if (!isStringAnswer(answer)) {
        console.warn(`Expected date answer but got ${typeof answer}`, answer);
        return <Typography className="text-xs italic text-[#666]">N/A - invalid answer</Typography>;
    }
    return isEmptyAnswer(answer)
        ? <Typography className="text-xs italic text-[#666]">(Not provided)</Typography>
        : <Typography className="text-xs text-[#111]">{dayjs(answer).format('DD/MM/YYYY')}</Typography>;
};

const displayString = (answer: IAnswer) => {
    if (!isStringAnswer(answer)) {
        console.warn(`Expected string answer but got ${typeof answer}`, answer);
        return <Typography className="text-xs italic text-[#666]">N/A - invalid answer</Typography>;
    }
    return isEmptyAnswer(answer)
        ? <Typography className="text-xs italic text-[#666]">(Not provided)</Typography>
        : <Typography className="whitespace-pre-wrap text-xs text-[#111]">{String(answer)}</Typography>;
};

const displayFiles = (attachments: IApplicationAttachment[]) => {
    return attachments.length > 0
        ? <FileAttachmentList attachments={attachments} canEdit={false} />
        : <Typography className="text-xs italic text-[#666]">(no file uploaded)</Typography>;
};