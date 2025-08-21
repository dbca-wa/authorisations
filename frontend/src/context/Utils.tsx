import type { AxiosError } from "axios";
import React from "react";

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


export const scrollToTop = (dependencies: React.DependencyList = []) => {
    React.useEffect(() => {
        window.scrollTo(0, 0);
    }, dependencies);
}
