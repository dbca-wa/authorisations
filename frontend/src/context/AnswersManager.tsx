import type { IAnswers } from "./types/Application";


export class AnswersManager {
    private static getItem(key: string): IAnswers | null {
        const item = localStorage.getItem(key);
        return item ? JSON.parse(item) : null;
    }

    private static setItem(key: string, value: IAnswers): void {
        localStorage.setItem(key, JSON.stringify(value));
    }

    private static getKey(applicationId: string): string {
        return `answers_${applicationId}`;
    }

    public static getAnswers(applicationId: string): IAnswers {
        // console.log("Getting answers for application ID:", applicationId);
        const key = this.getKey(applicationId);
        return this.getItem(key) || {};
    }

    public static setAnswers(applicationId: string, answers: IAnswers): void {
        const key = this.getKey(applicationId);
        this.setItem(key, answers);
    }
}
