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
import { RESPONSE_404 } from './context/Constants';
import type { IRoute } from './context/Types';
import { NewApplication } from './components/layout/main/NewApplication';

// Guards
// const authGuard = () => {
// 	const authStore = getAuthStore();
// 	if (!authStore.isAuthenticated) {
// 		return redirect("/auth/login");
// 	}
// 	return null;
// };

// const guestGuard = () => {
// 	const authStore = getAuthStore();
// 	if (authStore.isAuthenticated) {
// 		return redirect("/");
// 	}
// 	return null;
// };

// const adminGuard = () => {
// 	const authStore = getAuthStore();
// 	// default auth guard
// 	if (!authStore.isAuthenticated) {
// 		return redirect("/auth/login");
// 	}
// 	// Prevent access for non-admins by redirecting to dashboard
// 	if (!authStore.isAdmin) {
// 		return redirect("/");
// 	}
// 	return null;
// };


// Routes for the application (text, path and icon)
export const ROUTES: IRoute[] = [
	{
		label: "My Applications",
		path: "/my-applications",
		icon: <TopicIcon />,
		divider: false,
	},
	{
		label: "New Application",
		path: "/new-application",
		icon: <CreateNewFolderIcon />,
		component: NewApplication,
		divider: true,
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
const getJsonData = async () => {
	const dataElement = document.getElementById('json-data');

	if (!dataElement || !dataElement.textContent) {
		throw RESPONSE_404;
	}

	return JSON.parse(dataElement.textContent);
}

async function getQuestionnaire() {
	const questionnaire = await getJsonData();
	// Check if the required fields are present
	if (!questionnaire.slug || !questionnaire.version || !questionnaire.name || !questionnaire.document) {
		throw RESPONSE_404;
	}

	return questionnaire;
}

export const router = createBrowserRouter(
	[
		// Add routes from ROUTES constant
		...ROUTES.map(route => ({
			path: route.path,
			element: <MainLayout route={route} />,
			loader: async ({ }: LoaderFunctionArgs) => {
				// Simulate fetching data from a API
				return await getJsonData();
			},
			errorElement: <ErrorPage />,
		})),

		// Other routes
		...[
			{
				path: "/q/:slug",
				Component: FormLayout,
				// loader: async ({ params }: LoaderFunctionArgs) => {
				loader: async ({ }: LoaderFunctionArgs) => {
					// Simulate fetching data from a API
					return await getQuestionnaire();
				},
				errorElement: <ErrorPage />,
			},
		],
	]
);
