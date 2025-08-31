import Button from "@mui/material/Button";
import { isRouteErrorResponse, Link, useRouteError } from "react-router";

export const ErrorPage = () => {
	const error = useRouteError();

	let errorMessage = "An unexpected error has occurred";
	let statusText = "Sorry, something went wrong";
	let status = "";

	if (isRouteErrorResponse(error)) {
		// console.log("Route Error Response:", error);
		errorMessage = error.data?.message || error.statusText;
		statusText = error.statusText;
		status = String(error.status);
	} else if (error instanceof Error) {
		errorMessage = error.message;
	} else if (typeof error === "string") {
		errorMessage = error;
	}

	return (
		<div className="h-screen w-screen flex items-center justify-center text-center">
			<div className="space-y-8">
				<h1 className="text-4xl">
					{status ? `${status} - ${statusText}` : statusText}
				</h1>

				<p className="text-xl">
					{errorMessage}
				</p>

				<div className="flex flex-col space-y-2 sm:flex-row sm:space-y-0 sm:space-x-3 justify-center">
					<Button variant="outlined" color="primary" size="large">
						<Link to="/">Home page</Link>
					</Button>
				</div>
			</div>
		</div>
	);
}