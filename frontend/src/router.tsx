import ChecklistRtlIcon from '@mui/icons-material/ChecklistRtl';
import CreateNewFolderIcon from '@mui/icons-material/CreateNewFolder';
import RateReviewIcon from '@mui/icons-material/RateReview';
import SettingsIcon from '@mui/icons-material/Settings';
import TopicIcon from '@mui/icons-material/Topic';

import type { LoaderFunctionArgs } from 'react-router';
import { createBrowserRouter } from "react-router";
import { ErrorPage } from "./components/layout/ErrorPage";
import { FormLayout } from "./components/layout/form/FormLayout";
import { MainLayout } from "./components/layout/main/MainLayout";
import { MyApplications } from './components/layout/main/MyApplications';
import { NewApplication } from './components/layout/main/NewApplication';
import { ApplicationAssessment } from './components/layout/main/Assessment';
import { ApiManager } from './context/ApiManager';
import type { IRoute, LoaderData } from "./context/types/Generic";
import { handleApiError } from './context/Utils';



/**
 * Factory that produces a route loader for the main layout.
 * Awaits processes (needed immediately for the sidebar) and optionally
 * kicks off questionnaire and/or application fetches as unblocked promises,
 * so routes that don't need a dataset never trigger its request.
 */
const mainLoader = (options: { questionnaires?: boolean; applications?: boolean } = {}) =>
	async (): Promise<LoaderData> => {
		const processes = await ApiManager
			.fetchAuthorisationProcesses()
			.catch(handleApiError);

		// Only start each fetch when the route has declared it needs the data.
		const questionnaires = options.questionnaires
			? ApiManager.fetchQuestionnaires().catch(handleApiError)
			: undefined;

		const applications = options.applications
			? ApiManager.fetchApplications().catch(handleApiError)
			: undefined;

		return { processes, questionnaires, applications };
	};

// Routes for the application (text, path and icon)
export const ROUTES: IRoute[] = [
	{
		label: "My applications",
		path: "/my-applications",
		icon: <TopicIcon />,
		divider: false,
		component: MyApplications,
		loader: mainLoader({ applications: true }),
	},
	{
		label: "New application",
		path: "/new-application",
		icon: <CreateNewFolderIcon />,
		divider: true,
		component: NewApplication,
		loader: mainLoader({ questionnaires: true }),
	},
	{
		label: "Assessment",
		path: "/assessment",
		icon: <ChecklistRtlIcon />,
		divider: true,
		component: ApplicationAssessment,
		condition: (processes) => processes.some((process) => process.can_review),
		loader: async (): Promise<LoaderData> => {
			const processes = await ApiManager
				.fetchAuthorisationProcesses()
				.catch(handleApiError);

			const applications = ApiManager
				.fetchAssessmentApplications()
				.catch(handleApiError);

			return { processes, applications };
		},
	},
	{
		label: "Settings",
		path: "/settings",
		icon: <SettingsIcon />,
		divider: false,
		// No data beyond processes is needed on this page.
		loader: mainLoader(),
	},
	{
		label: "Feedback",
		// Opened directly by the sidebar via window.open; not registered as a React Router route.
		path: "mailto:ecoinformatics.admin@dbca.wa.gov.au?subject=Feedback on Authorisations System",
		icon: <RateReviewIcon />,
		divider: false,
		external: true,
	},
];

const formLayoutLoader = async ({ params }: LoaderFunctionArgs) => {
	const app = await ApiManager
		.getApplication(params.key!)
		.catch(handleApiError);

	const questionnaire = await ApiManager
		.getQuestionnaire(app.questionnaire_id)
		.catch(handleApiError);

	const attachments = await ApiManager
		.getApplicationAttachments(params.key!)
		.catch(handleApiError);

	return { app, questionnaire, attachments };
}

export const router = createBrowserRouter(
	[
		// Register only internal (non-external) routes with React Router.
		// External routes (e.g. mailto: links) are handled directly by the sidebar.
		...ROUTES.filter(route => !route.external).map(route => ({
			path: route.path,
			element: <MainLayout route={route} />,
			loader: route.loader,
			errorElement: <ErrorPage />,
		})),

		// Application form
		...[
			{
				path: "/a/:key",
				element: <FormLayout />,
				errorElement: <ErrorPage />,
				loader: formLayoutLoader,
			},
		],
	]
);
