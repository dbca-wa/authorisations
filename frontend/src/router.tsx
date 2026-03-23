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
import { ReviewApplications } from './components/layout/main/ReviewApplications';
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
			const processes = await ApiManager
				.fetchAuthorisationProcesses()
				.catch(handleApiError);
			
			const questionnaires = ApiManager
				.fetchQuestionnaires()
				.catch(handleApiError);

			const applications = ApiManager
				.fetchApplications()
				.catch(handleApiError);
			

			return { processes, questionnaires, applications };
		},
	},
	{
		label: "New application",
		path: "/new-application",
		icon: <CreateNewFolderIcon />,
		divider: true,
		component: NewApplication,
		loader: async () => {
			const processes = await ApiManager
				.fetchAuthorisationProcesses()
				.catch(handleApiError);
			
			const questionnaires = ApiManager
				.fetchQuestionnaires()
				.catch(handleApiError);

			const applications = ApiManager
				.fetchApplications()
				.catch(handleApiError);
			

			return { processes, questionnaires, applications };
		},
	},
	{
		label: "Review",
		path: "/review-applications",
		icon: <ChecklistRtlIcon />,
		divider: true,
		component: ReviewApplications,
		condition: (processes) => processes.some((process) => process.can_review),
		loader: async () => {
			const processes = await ApiManager
				.fetchAuthorisationProcesses()
				.catch(handleApiError);
			
			const questionnaires = ApiManager
				.fetchQuestionnaires()
				.catch(handleApiError);

			const applications = ApiManager
				.fetchApplications()
				.catch(handleApiError);
			

			return { processes, questionnaires, applications };
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
		.getQuestionnaire(app.questionnaire_id)
		.catch(handleApiError);

	const attachments = await ApiManager
		.getApplicationAttachments(params.key!)
		.catch(handleApiError);

	return { app, questionnaire, attachments };
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
