import type { AxiosRequestConfig } from "axios";
import axios from "axios";
import { ConfigManager } from "./ConfigManager";
import type { IApplicationData } from "./types/Application";


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
            baseURL: clientConfig.base_url,
            headers: {
                'Content-Type': 'application/json',
                // Allow dynamic string keys for headers
            } as { [key: string]: string }
        }

        // Set the CSRF token header
        requestConfig.headers[clientConfig.csrf_header] = clientConfig.csrf_token;

        return requestConfig;

    }

    public static async fetchApplications(): Promise<IApplicationData[]> {
        const requestConfig = ApiManager.getRequestConfig();
        const response = await axios.get<IApplicationData[]>("applications/", requestConfig);
        
        return response.data;
    }

    public static async createApplication(questionnaireSlug: string): Promise<IApplicationData> {
        const requestConfig = ApiManager.getRequestConfig();
        const response = await axios.post<IApplicationData>("applications/", {
            questionnaire_slug: questionnaireSlug,
            // document: {
            //     "answers": {"0-0-0": "Hello :)"},
            // },
        }, requestConfig);

        return response.data;
    }
}
