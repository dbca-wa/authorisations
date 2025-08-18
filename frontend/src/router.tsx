import CreateNewFolderIcon from '@mui/icons-material/CreateNewFolder';
import RateReviewIcon from '@mui/icons-material/RateReview';
import SettingsIcon from '@mui/icons-material/Settings';
import TopicIcon from '@mui/icons-material/Topic';


// router.tsx with error handling
import type { LoaderFunctionArgs } from 'react-router';
import { createBrowserRouter } from "react-router";
import { ErrorPage } from "./components/layout/ErrorPage";
import { FormLayout } from "./components/layout/form/FormLayout";
import { MainLayout } from "./components/layout/main/MainLayout";
import { MyApplications } from './components/layout/main/MyApplications';
import { NewApplication } from './components/layout/main/NewApplication';
import { ApiManager } from './context/ApiManager';
import type { IApplicationData } from './context/types/Application';
import type { IRoute } from "./context/types/Generic";
import { getResponse, handleApiError } from './context/Utils';

// Routes for the application (text, path and icon)
export const ROUTES: IRoute[] = [
	{
		label: "My Applications",
		path: "/my-applications",
		icon: <TopicIcon />,
		divider: false,
		component: MyApplications,
		loader: async () => {
			return await ApiManager.fetchApplications().catch(handleApiError);
		},
	},
	{
		label: "New Application",
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


// Temporary function to mimic an API call
// const getJsonData = async () => {
// 	const dataElement = document.getElementById('json-data');

// 	if (!dataElement || !dataElement.textContent) {
// 		throw getResponse(
// 			404,
// 			"Not Found",
// 			"This document cannot be found or you may not have the permission to view it."
// 		);
// 	}

// 	return JSON.parse(dataElement.textContent);
// }

// const getQuestionnaire = async () => {
// 	const questionnaire = await getJsonData();
// 	// Check if the required fields are present
// 	if (!questionnaire.slug || !questionnaire.version || !questionnaire.name || !questionnaire.document) {
// 		throw RESPONSE_404;
// 	}

// 	return questionnaire;
// }

export const router = createBrowserRouter(
	[
		// Add routes from ROUTES constant
		...ROUTES.map(route => ({
			path: route.path,
			element: <MainLayout route={route} />,
			// loader: route.loader ? route.loader : getJsonData,
			loader: route.loader,
			errorElement: <ErrorPage />,
		})),

		// Application editing route
		...[
			{
				path: "/a/:key",
				Component: FormLayout,
				errorElement: <ErrorPage />,
				loader: async ({ params }: LoaderFunctionArgs) => {
					const app = await ApiManager
						.getApplication(params.key!)
						.catch(handleApiError);

					const questionnaire = await ApiManager
						.getQuestionnaire(app.questionnaire_slug, app.questionnaire_version)
						.catch(handleApiError);

					return { app, questionnaire };
				},
			},
		],
	]
);
