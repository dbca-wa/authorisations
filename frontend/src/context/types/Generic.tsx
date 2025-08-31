import type { LoaderFunctionArgs } from "react-router";

export type PrimitiveType = string | number | boolean | null;

export interface IRoute {
    label: string;
    path: string;
    icon: React.ReactNode;
    divider: boolean;
    component?: React.ComponentType<any>;
    loader?: (params: LoaderFunctionArgs) => Promise<any>;
}

