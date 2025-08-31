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
import { ApiManager } from './context/ApiManager';
import type { IRoute } from "./context/types/Generic";
import { handleApiError } from './context/Utils';

// Routes for the application (text, path and icon)
export const ROUTES: IRoute[] = [
	{
		label: "My applications",
		path: "/my-applications",
		icon: <TopicIcon />,
		divider: false,
		component: MyApplications,
		loader: async () => {
			return await ApiManager.fetchApplications().catch(handleApiError);
		},
	},
	{
		label: "New application",
		path: "/new-application",
		icon: <CreateNewFolderIcon />,
		divider: true,
		component: NewApplication,
		loader: async () => {
			return await ApiManager.fetchQuestionnaires().catch(handleApiError);
		},
	},
	{
		label: "Settings",
		path: "/settings",
		icon: <SettingsIcon />,
		divider: false,
	},
	{
		label: "Feedback",
		path: "mailto:ecoinformatics.admin@dbca.wa.gov.au?subject=Feedback on Authorisations Application",
		icon: <RateReviewIcon />,
		divider: false,
	},
];

const formLayoutLoader = async ({ params }: LoaderFunctionArgs) => {
	const app = await ApiManager
		.getApplication(params.key!)
		.catch(handleApiError);

	const questionnaire = await ApiManager
		.getQuestionnaire(app.questionnaire_slug, app.questionnaire_version)
		.catch(handleApiError);

	return { app, questionnaire };
}

export const router = createBrowserRouter(
	[
		// Add routes from ROUTES constant
		...ROUTES.map(route => ({
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
