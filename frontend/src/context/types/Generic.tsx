import type { LoaderFunctionArgs } from "react-router";
import type { IAuthorisationProcess, IQuestionnaireData } from "./Questionnaire";
import type { IApplicationData } from "./Application";

export type PrimitiveType = string | number | boolean | null;

export type LoaderData = {
	processes: IAuthorisationProcess[];
	questionnaires: Promise<IQuestionnaireData[]>;
	applications: Promise<IApplicationData[]>;
}

export interface IRoute {
    label: string;
    path: string;
    icon: React.ReactNode;
    divider: boolean;
    component?: React.ComponentType<any>;
    condition?: (processes: IAuthorisationProcess[]) => boolean;
    loader?: (params: LoaderFunctionArgs) => Promise<LoaderData>;
}

export type AsyncVoidAction = () => Promise<void>;

export type NumberedBooleanObj = { [key: number]: boolean };
