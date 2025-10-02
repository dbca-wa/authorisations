import _ from "underscore";

export interface IConfig {
    api_base: string;
    csrf_header: string;
    csrf_token: string;
    upload_max_size: number; // in bytes
    // list of allowed mime types for uploaded files
    upload_mime_types: string[];
}

export class ConfigManager {
    private static _config: IConfig | null = null;

    public static get(): IConfig {
        if (this._config !== null) return _.clone(this._config);

        const dataElement = document.getElementById('config');

        if (!dataElement || !dataElement.textContent) {
            throw new Error("Config data not found in the document.");
        }

        const base64str = JSON.parse(dataElement.textContent);
        this._config = JSON.parse(window.atob(base64str)) as IConfig;

        // TODO: Do better interface validation 
        // (maybe use a library like zod, joi or yup)
        if (typeof this._config !== 'object') {
            throw new TypeError("Config data is not an object.");
        }

        console.log("Config parsed:", this._config)
        return _.clone(this._config);
    }
}