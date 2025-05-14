import Button from "@mui/material/Button";
import { isRouteErrorResponse, Link, useRouteError } from "react-router";

export default function ErrorPage() {
	const error = useRouteError();

	let errorMessage = "An unexpected error has occurred";
	let statusText = "Sorry, something went wrong";
	let status = "";

	if (isRouteErrorResponse(error)) {
		errorMessage = error.data?.message || error.statusText;
		statusText = error.statusText;
		status = String(error.status);
	} else if (error instanceof Error) {
		errorMessage = error.message;
	} else if (typeof error === "string") {
		errorMessage = error;
	}

	return (
		<div className="h-screen flex flex-col items-center justify-center p-6 text-center">
			<div className="space-y-6 max-w-md">
				<h1 className="text-4xl font-bold text-gray-900 dark:text-white">
					{status ? `${status} - ${statusText}` : statusText}
				</h1>

				<p className="text-lg text-gray-600 dark:text-gray-400">
					{errorMessage}
				</p>

				<div className="flex flex-col space-y-2 sm:flex-row sm:space-y-0 sm:space-x-3 justify-center">
					<Button variant="outlined">
						<Link to="/">Home page</Link>
					</Button>
				</div>
			</div>
		</div>
	);
}