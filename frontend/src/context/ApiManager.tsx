import type { AxiosRequestConfig } from "axios";
import axios from "axios";
import { ConfigManager } from "./ConfigManager";
import type { IApplicationData, IFormDocument } from "./types/Application";
import type { IQuestionnaireData } from "./types/Questionnaire";


export class ApiManager {
    private constructor() {
        // Private constructor to prevent instantiation
    }

    private static getRequestConfig(): AxiosRequestConfig {
        const clientConfig = ConfigManager.get();
        const requestConfig = {
            withCredentials: false,
            withXSRFToken: true,
            xsrfHeaderName: clientConfig.csrf_header,
            baseURL: clientConfig.api_base,
            headers: {
                'Content-Type': 'application/json',
                // Allow dynamic string keys for headers
            } as { [key: string]: string }
        }

        // Set the CSRF token header
        requestConfig.headers[clientConfig.csrf_header] = clientConfig.csrf_token;

        return requestConfig;
    }

    public static async getApplication(key: string): Promise<IApplicationData> {
        const requestConfig = ApiManager.getRequestConfig();
        const response = await axios.get<IApplicationData>(`/applications/${key}`, requestConfig);

        return response.data;
    }

    public static async fetchApplications(): Promise<IApplicationData[]> {
        const requestConfig = ApiManager.getRequestConfig();
        const response = await axios.get<IApplicationData[]>("/applications", requestConfig);

        return response.data;
    }

    public static async createApplication(questionnaireSlug: string): Promise<IApplicationData> {
        const requestConfig = ApiManager.getRequestConfig();
        const response = await axios.post<IApplicationData>("/applications", {
            questionnaire_slug: questionnaireSlug,
        }, requestConfig);

        return response.data;
    }

    public static async updateApplication(key: string, document: IFormDocument): Promise<IApplicationData> {
        const requestConfig = ApiManager.getRequestConfig();
        const response = await axios.put<IApplicationData>(
            `/applications/${key}`, { document: document }, requestConfig);

        return response.data;
    }

    public static async getQuestionnaire(slug: string, version: number): Promise<IQuestionnaireData> {
        const requestConfig = ApiManager.getRequestConfig();
        const url = `/questionnaires/${slug}` + (version ? `?version=${version}` : '');
        const response = await axios.get<IQuestionnaireData>(url, requestConfig);

        return response.data;
    }

    public static async fetchQuestionnaires(): Promise<IQuestionnaireData[]> {
        const requestConfig = ApiManager.getRequestConfig();
        const response = await axios.get<IQuestionnaireData[]>("/questionnaires", requestConfig);

        return response.data;
    }
}
