// router.tsx with error handling
import { createBrowserRouter } from "react-router";

// Layouts
import { MainLayout } from "./components/layout/MainLayout";
// import AuthLayout from "@/components/layout/AuthLayout";
// import MainLayout from "@/components/layout/MainLayout";

// Pages
// import Login from "@/routes/auth/Login";
// import Register from "@/routes/auth/Register";
// import Home from "@/routes/dashboard/Home";
// import Users from "@/routes/users/Users";
// import UserDetail from "@/routes/users/UserDetail";
// import Submissions from "@/routes/submissions/Submissions";
// import SubmissionDetail from "@/routes/submissions/SubmissionDetail";
// import AdminPage from "./routes/admin/AdminPage";

// Store utils
// import { getAuthStore } from "./stores/storeUtils";

// Error component
import ErrorPage from "./components/ErrorPage";

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

export const router = createBrowserRouter([
	{
		// path: import.meta.env.BASE_URL + "aec",
		path: "/a/aec",
		Component: MainLayout,
		errorElement: <ErrorPage />,
	},
	// {
	// 	path: "/",
	// 	// errorElement: <ErrorPage />,
	// 	children: [
	// 		// Auth routes (for non-authenticated users)
	// 		{
	// 			path: "auth",
	// 			element: <AuthLayout />,
	// 			loader: guestGuard,
	// 			errorElement: <ErrorPage />,
	// 			children: [
	// 				{ path: "login", element: <Login /> },
	// 				{ path: "register", element: <Register /> },
	// 			],
	// 		},

	// 		// Protected routes (for authenticated users)
	// 		{
	// 			element: <MainLayout />,
	// 			loader: authGuard,
	// 			errorElement: <ErrorPage />,
	// 			children: [
	// 				{ index: true, element: <Home /> },
	// 				{
	// 					path: "users",
	// 					children: [
	// 						{ index: true, element: <Users /> },
	// 						{ path: ":id", element: <UserDetail /> },
	// 					],
	// 				},
	// 				{
	// 					path: "submissions",
	// 					children: [
	// 						{ index: true, element: <Submissions /> },
	// 						{ path: ":id", element: <SubmissionDetail /> },
	// 					],
	// 				},
	// 				{
	// 					path: "admin",
	// 					element: <AdminPage />,
	// 					loader: adminGuard,
	// 				},
	// 			],
	// 		},
	// 	],
	// },
]);