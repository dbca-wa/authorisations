
export type PrimitiveType = string | number | boolean | null;

export interface IRoute {
    label: string;
    path: string;
    icon: React.ReactNode;
    component?: React.ComponentType<any>;
    divider: boolean;
}

