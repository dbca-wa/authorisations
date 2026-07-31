import axios from "axios";

import type { AxiosProgressEvent, AxiosRequestConfig } from "axios";
import { ConfigManager } from "./ConfigManager";
import type { ApplicationStatus, IApplicationAttachment, IApplicationData, IFormDocument } from "./types/Application";
import type { IAuthorisationProcess, IQuestionnaireData } from "./types/Questionnaire";


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
            } as { [key: string]: string },
            // Avoid buffering the entire stream for large files
            maxRedirects: 0,
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
        // console.debug("Fetching applications...");
        const response = await axios.get<IApplicationData[]>("/applications", requestConfig);
        // console.debug("Fetched applications:", response.data.length);

        return response.data;
    }

    public static async createApplication({
        processSlug,
        questionnaireId,
        questionnaireCode,
        questionnaireVersion,
        privacyConsentAgreed,
        turnstileToken,
    }: {
        processSlug: string;
        questionnaireId: number;
        questionnaireCode: string;
        questionnaireVersion: number;
        privacyConsentAgreed: boolean;
        turnstileToken: string;
    }): Promise<IApplicationData> {
        const requestConfig = ApiManager.getRequestConfig();
        const response = await axios.post<IApplicationData>("/applications", {
            process_slug: processSlug,
            questionnaire_id: questionnaireId,
            questionnaire_code: questionnaireCode,
            questionnaire_version: questionnaireVersion,
            privacy_consent_agreed: privacyConsentAgreed,
            turnstile_token: turnstileToken,
        }, requestConfig);

        return response.data;
    }

    public static async updateApplication(key: string, document: IFormDocument): Promise<IApplicationData> {
        const requestConfig = ApiManager.getRequestConfig();
        const response = await axios.put<IApplicationData>(
            `/applications/${key}`, { document: document }, requestConfig);

        return response.data;
    }

    public static async submitApplication(key: string, turnstileToken: string): Promise<IApplicationData> {
        const requestConfig = ApiManager.getRequestConfig();
        const response = await axios.patch<IApplicationData>(
            `/applications/${key}`,
            {
                status: "SUBMITTED",
                turnstile_token: turnstileToken,
            },
            requestConfig,
        );

        return response.data;
    }

    public static async discardApplication(key: string): Promise<IApplicationData> {
        const requestConfig = ApiManager.getRequestConfig();
        const response = await axios.patch<IApplicationData>(
            `/applications/${key}`,
            { status: "DISCARDED" },
            requestConfig,
        );

        return response.data;
    }

    public static async revertDiscardedApplication(key: string): Promise<IApplicationData> {
        const requestConfig = ApiManager.getRequestConfig();
        const response = await axios.patch<IApplicationData>(
            `/applications/${key}`,
            { status: "DRAFT" },
            requestConfig,
        );

        return response.data;
    }

    public static async getApplicationAttachments(appKey: string): Promise<IApplicationAttachment[]> {
        const requestConfig = ApiManager.getRequestConfig();
        const response = await axios.get<IApplicationAttachment[]>(
            `/attachments?application_key=${appKey}`, requestConfig);

        return response.data;
    }

    public static async uploadAttachment({
        appKey, name, question, file, signal, callback,
    }: {
        appKey: string;
        name: string;
        question: string;
        file: File;
        signal?: AbortSignal;
        callback?: (event: AxiosProgressEvent) => void;
    }): Promise<IApplicationAttachment> {
        const requestConfig = ApiManager.getRequestConfig();

        // We need to send multipart/form-data
        requestConfig.headers!['Content-Type'] = 'multipart/form-data';

        // Attach the abort signal to allow cancelling upload
        requestConfig.signal = signal;

        //  Attach to upload progress 
        requestConfig.onUploadProgress = callback;

        // Create form data
        const formData = new FormData();
        formData.append("application_key", appKey);
        formData.append("name", name);
        formData.append("question", question);
        formData.append("file", file);

        // Start the upload
        const response = await axios.post<IApplicationAttachment>(
            `/attachments`, formData, requestConfig);

        return response.data;
    }

    public static async deleteAttachment(attachmentKey: string): Promise<void> {
        const requestConfig = ApiManager.getRequestConfig();
        await axios.delete(`/attachments/${attachmentKey}`, requestConfig);
    }

    public static async renameAttachment(attachmentKey: string, newName: string): Promise<IApplicationAttachment> {
        const requestConfig = ApiManager.getRequestConfig();
        const response = await axios.patch<IApplicationAttachment>(
            `/attachments/${attachmentKey}`, { name: newName }, requestConfig);

        return response.data;
    }

    public static async getQuestionnaire(id: number): Promise<IQuestionnaireData> {
        const requestConfig = ApiManager.getRequestConfig();
        const url = `/questionnaires/${id}`;
        const response = await axios.get<IQuestionnaireData>(url, requestConfig);

        return response.data;
    }

    public static async fetchQuestionnaires(): Promise<IQuestionnaireData[]> {
        const requestConfig = ApiManager.getRequestConfig();
        // console.debug("Fetching questionnaires...");
        const response = await axios.get<IQuestionnaireData[]>("/questionnaires", requestConfig);
        // console.debug("Fetched questionnaires:", response.data.length);

        return response.data;
    }

    public static async fetchAuthorisationProcesses(): Promise<IAuthorisationProcess[]> {
        const requestConfig = ApiManager.getRequestConfig();
        // console.debug("Fetching processes...");
        const response = await axios.get<IAuthorisationProcess[]>("/processes", requestConfig);
        // console.debug("Fetched processes:", response.data.length);

        return response.data;
    }

    public static async fetchReviewQueueApplications(): Promise<IApplicationData[]> {
        const requestConfig = ApiManager.getRequestConfig();
        const response = await axios.get<IApplicationData[]>("/review", requestConfig);

        return response.data;
    }

    /**
     * Update the status of an application in the review queue.
     * Sends a PATCH request to advance the application through review workflow states.
     * Transition validity is enforced by the backend serialiser.
     *
     * @param key - The application key (UUID)
     * @param status - The target status (must be a valid reviewer-initiated transition)
     * @returns The updated application data
     * @throws AxiosError if the transition is invalid or user lacks reviewer permissions
     */
    public static async updateReviewerApplicationStatus(
        key: string,
        status: ApplicationStatus,
    ): Promise<IApplicationData> {
        const requestConfig = ApiManager.getRequestConfig();
        const response = await axios.patch<IApplicationData>(
            `/review/${key}`,
            { status },
            requestConfig,
        );

        return response.data;
    }
}
