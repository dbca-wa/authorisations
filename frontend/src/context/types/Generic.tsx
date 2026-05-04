import type { LoaderFunctionArgs } from "react-router";
import type { IAuthorisationProcess, IQuestionnaireData } from "./Questionnaire";
import type { IApplicationData } from "./Application";

export type PrimitiveType = string | number | boolean | null;

export type LoaderData = {
	processes: IAuthorisationProcess[];
	/** Omitted when the route does not need questionnaire data. */
	questionnaires?: Promise<IQuestionnaireData[]>;
	/** Omitted when the route does not need application data. */
	applications?: Promise<IApplicationData[]>;
}

export interface IRoute {
    label: string;
    path: string;
    icon: React.ReactNode;
    divider: boolean;
    component?: React.ComponentType<object>;
    condition?: (processes: IAuthorisationProcess[]) => boolean;
    loader?: (params: LoaderFunctionArgs) => Promise<LoaderData>;
    /** When true, the route is an external link (e.g. mailto:) and must not be registered with React Router. */
    external?: boolean;
    /** When false, the route is hidden from the sidebar and can be rendered elsewhere (e.g. footer). */
    sidebar?: boolean;
}

export type AsyncVoidAction = () => Promise<void>;

export type NumberedBooleanObj = { [key: number]: boolean };
