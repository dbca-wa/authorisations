import { styled } from "@mui/material/styles";
import type { AxiosError } from "axios";
import type { ReactElement } from "react";

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
 * Helper to get file icon based on its extension. 
 * 
 * @param fileName 
 * @returns icon name for the file type or a default icon if the type is not recognized
 */
export const getIconFromFilename = (filename: string): ReactElement => {
    const extension = filename.split('.').pop()?.toLowerCase();
    switch (extension) {
        case 'pdf':
            return <span className="iconify-color vscode-icons--file-type-pdf2"></span>;
        case 'doc':
        case 'docx':
            return <span className="iconify-color vscode-icons--file-type-word"></span>;
        case 'xls':
        case 'xlsx':
            return <span className="iconify-color vscode-icons--file-type-excel"></span>;
        case 'png':
        case 'jpg':
        case 'jpeg':
            return <span className="iconify-color flat-color-icons--image-file"></span>;
        // Default file icon for unrecognized types
        default:
            return <span className="iconify-color flat-color-icons--file"></span>;
    }
}