import type { AxiosError } from "axios";

// Simple browser-safe assert
export function assert(condition: boolean, message: string): void {
    if (import.meta.env.DEV && !condition) {
        throw new Error(message);
    }
}

export const getResponse = (status: number, statusText: string, message: string) => {
    return Response.json(
        { message: message },
        { status: status, statusText: statusText }
    )
};

export const handleApiError = (error: AxiosError) => {
    if (import.meta.env.DEV) {
        console.error('Error while fetching applications:', error);
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
    const elementId = `q-${stepIndex}-${sectionIndex}-${questionIndex}`;
    const element = document.getElementById(elementId) as HTMLElement;

    if (element) {
        element.scrollIntoView({ behavior: "smooth", block: "center" });
    }
}

export const openExternalWindow = (url: string, name: string = "_blank") => {
    window.open(
        url, // link
        `auth_${name}`, // window name
        "toolbar=no, menubar=no, location=no, status=no, resizable=yes, scrollbars=yes"
    );
}

export const sleep = (ms: number) => new Promise( resolve => setTimeout(resolve, ms) );

