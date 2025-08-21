import type { IAnswers } from "./types/Application";


export class LocalStorage {
    private static getItem(key: string): IAnswers | null {
        const item = localStorage.getItem(key);
        return item ? JSON.parse(item) : null;
    }

    private static setItem(key: string, value: IAnswers): void {
        localStorage.setItem(key, JSON.stringify(value));
    }

    private static getAnswersKey(applicationKey: string): string {
        return `answers_${applicationKey}`;
    }

    public static getAnswers(applicationKey: string): IAnswers {
        // console.log("Getting answers for application:", applicationKey);
        const key = this.getAnswersKey(applicationKey);
        return this.getItem(key) || {};
    }

    public static setAnswers(applicationKey: string, answers: IAnswers): void {
        const key = this.getAnswersKey(applicationKey);
        this.setItem(key, answers);
    }
}
