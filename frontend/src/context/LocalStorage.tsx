import type { IFormDocument } from "./types/Application";


export class LocalStorage {
    private static getItem(key: string): object | null {
        const item = localStorage.getItem(key);
        return item ? JSON.parse(item) : null;
    }

    private static setItem(key: string, value: object): void {
        localStorage.setItem(key, JSON.stringify(value));
    }

    private static getKey(key: string): string {
        return `auth_${key}`;
    }

    public static getValue<T>(key: string): T | null {
        return this.getItem(this.getKey(key)) as T | null;
    }

    public static setValue<T>(key: string, value: T): void {
        this.setItem(this.getKey(key), value as unknown as object);
    }

    public static getFormState(applicationKey: string): IFormDocument | null {
        // console.log("Getting answers for application:", applicationKey);
        const key = this.getKey(applicationKey);
        return this.getItem(key) as IFormDocument | null;
    }

    public static setFormState(applicationKey: string, document: IFormDocument): void {
        const key = this.getKey(applicationKey);
        this.setItem(key, document);
    }
}
