import type { IFormDocument } from "./types/Application";


export class LocalStorage {
    /** Resolve browser storage safely for both app runtime and Node-based tests. */
    private static getStorage(): Storage | null {
        if (typeof window === "undefined") {
            return null;
        }

        return window.localStorage ?? null;
    }

    private static getItem(key: string): object | null {
        const storage = this.getStorage();
        const item = storage?.getItem(key);
        return item ? JSON.parse(item) : null;
    }

    private static setItem(key: string, value: object): void {
        const storage = this.getStorage();
        storage?.setItem(key, JSON.stringify(value));
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

    public static removeValue(key: string): void {
        const storage = this.getStorage();
        storage?.removeItem(this.getKey(key));
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
