import { styled } from "@mui/material/styles";
import type { AxiosError } from "axios";

// Simple browser-safe assert
export function assert(condition: boolean, message: string): void {
    if (import.meta.env.DEV && !condition) {
        throw new Error(message);
    }
}

const getResponse = (status: number, statusText: string, message: string) => {
    return Response.json(
        { message: message },
        { status: status, statusText: statusText }
    )
};

export const handleApiError = (error: AxiosError) => {
    if (import.meta.env.DEV) {
        console.error('API Error:', error);
    }

    throw getResponse(
        error.status!, error.response!.statusText, error.message);
};


export const scrollToTop = () => {
    window.scrollTo(0, 0);
}

export const scrollToQuestion = ({
    stepIndex, sectionIndex = 0, questionIndex = 0,
}: {
    stepIndex: number;
    sectionIndex?: number;
    questionIndex?: number;
}) => {
    const elementId = `q-${stepIndex}.${sectionIndex}-${questionIndex}`;
    const element = document.getElementById(elementId) as HTMLElement;

    if (element) {
        element.scrollIntoView({ behavior: "smooth", block: "center" });
    }
}

export const openNewTab = (url: string, name: string = "_blank") => {
    const newWindow = window.open(url, name, 'noopener');
    if (newWindow) {
        newWindow.opener = null;  // extra safety
        newWindow.focus();
    }
}

export const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));


export const VisuallyHiddenInput = styled('input')({
    clip: 'rect(0 0 0 0)',
    clipPath: 'inset(50%)',
    height: 1,
    overflow: 'hidden',
    position: 'absolute',
    bottom: 0,
    left: 0,
    whiteSpace: 'nowrap',
    width: 1,
    margin: '0!important',
});


/**
 * Helper to get mime type from file name extension. 
 * 
 * We do not assume on this function when uploading files, 
 * as the backend will determine the actual mime type from the "magic bytes".
 * This is just for display purposes and file icon on UI.
 * 
 * @param fileName 
 * @returns mime type string
 */
export const getMimeTypeFromFileName = (fileName: string): string => {
    const extension = fileName.split('.').pop()?.toLowerCase();
    switch (extension) {
        case 'pdf':
            return 'application/pdf';
        case 'doc':
            return 'application/msword';
        case 'docx':
            return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';
        case 'xls':
            return 'application/vnd.ms-excel';
        case 'xlsx':
            return 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';
        case 'png':
            return 'image/png';
        case 'jpg':
        case 'jpeg':
            return 'image/jpeg';
        default:
            return 'application/octet-stream'; // Default binary type
    }
}