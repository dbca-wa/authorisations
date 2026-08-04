import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ErrorPage } from "../../../../components/layout/ErrorPage";

/**
 * ErrorPage component tests.
 * 
 * Tests all error rendering paths: RouteErrorResponse with status/message,
 * Error instances, and string error messages. Ensures the component gracefully
 * handles different error types and displays appropriate messaging.
 */

// Global state for mock route errors
declare global {
	var mockRouteError: unknown;
}

vi.mock("react-router", async () => {
	const actual = await vi.importActual<typeof import("react-router")>("react-router");
	return {
		...actual,
		useRouteError: () => {
			// useRouteError is mocked per test via mockRouteError
			return globalThis.mockRouteError;
		},
	};
});

describe("ErrorPage", () => {
	beforeEach(() => {
		delete globalThis.mockRouteError;
	});

	describe("RouteErrorResponse errors", () => {
		it("renders error page without crashing", () => {
			globalThis.mockRouteError = {
				status: 404,
				statusText: "Not Found",
				data: { message: "The application you requested does not exist" },
			};

			render(
				<MemoryRouter>
					<ErrorPage />
				</MemoryRouter>,
			);

			expect(screen.getByRole("heading")).toBeInTheDocument();
		});

		it("renders with empty error data", () => {
			globalThis.mockRouteError = {
				status: 500,
				statusText: "Internal Server Error",
				data: {},
			};

			render(
				<MemoryRouter>
					<ErrorPage />
				</MemoryRouter>,
			);

			expect(screen.getByRole("heading")).toBeInTheDocument();
		});

		it("renders with null error data", () => {
			globalThis.mockRouteError = {
				status: 403,
				statusText: "Forbidden",
				data: null,
			};

			render(
				<MemoryRouter>
					<ErrorPage />
				</MemoryRouter>,
			);

			expect(screen.getByRole("heading")).toBeInTheDocument();
		});
	});

	describe("Error instances", () => {
		it("displays error message from Error instance", () => {
			globalThis.mockRouteError = new Error("Database connection failed");

			render(
				<MemoryRouter>
					<ErrorPage />
				</MemoryRouter>,
			);

			expect(screen.getByText("Database connection failed")).toBeInTheDocument();
		});

		it("displays custom error message from Error subclass", () => {
			class ApiError extends Error {
				constructor() {
					super("API request timed out");
				}
			}

			globalThis.mockRouteError = new ApiError();

		render(
			<MemoryRouter>
				<ErrorPage />
			</MemoryRouter>,
		);

			expect(screen.getByText("API request timed out")).toBeInTheDocument();
		});
	});

	describe("String error messages", () => {
		it("displays error message from string error", () => {
			globalThis.mockRouteError = "Session expired. Please log in again.";

			render(
				<MemoryRouter>
					<ErrorPage />
				</MemoryRouter>,
			);

			expect(screen.getByText("Session expired. Please log in again.")).toBeInTheDocument();
		});

		it("uses default status text for string errors", () => {
			globalThis.mockRouteError = "Network error";

			render(
				<MemoryRouter>
					<ErrorPage />
				</MemoryRouter>,
			);

			expect(screen.getByText("Sorry, something went wrong")).toBeInTheDocument();
			expect(screen.getByText("Network error")).toBeInTheDocument();
		});
	});

	describe("Fallback behavior", () => {
		it("displays default error message when error is undefined", () => {
			globalThis.mockRouteError = undefined;

			render(
				<MemoryRouter>
					<ErrorPage />
				</MemoryRouter>,
			);

			expect(screen.getByText("Sorry, something went wrong")).toBeInTheDocument();
			expect(screen.getByText("An unexpected error has occurred")).toBeInTheDocument();
		});

		it("displays default error message when error is null", () => {
			globalThis.mockRouteError = null;

			render(
				<MemoryRouter>
					<ErrorPage />
				</MemoryRouter>,
			);

			expect(screen.getByText("Sorry, something went wrong")).toBeInTheDocument();
			expect(screen.getByText("An unexpected error has occurred")).toBeInTheDocument();
		});

		it("displays default error message for unexpected error types (e.g., object)", () => {
			globalThis.mockRouteError = { custom: "error object" };

			render(
				<MemoryRouter>
					<ErrorPage />
				</MemoryRouter>,
			);

			expect(screen.getByText("Sorry, something went wrong")).toBeInTheDocument();
			expect(screen.getByText("An unexpected error has occurred")).toBeInTheDocument();
		});
	});

	describe("Navigation", () => {
		it("renders link to home page", () => {
			globalThis.mockRouteError = new Error("Page not found");

			render(
				<MemoryRouter>
					<ErrorPage />
				</MemoryRouter>,
			);

			const homeLink = screen.getByRole("link", { name: "Home page" });
			expect(homeLink).toBeInTheDocument();
			expect(homeLink).toHaveAttribute("href", "/");
		});

		it("displays link button even with status code errors", () => {
			globalThis.mockRouteError = {
				status: 401,
				statusText: "Unauthorized",
				data: { message: "Authentication required" },
			};

			render(
				<MemoryRouter>
					<ErrorPage />
				</MemoryRouter>,
			);

			expect(screen.getByRole("link", { name: "Home page" })).toBeInTheDocument();
		});
	});

	describe("Layout structure", () => {
		it("renders error content in centered container", () => {
			globalThis.mockRouteError = new Error("Test error");

			const { container } = render(
				<MemoryRouter>
					<ErrorPage />
				</MemoryRouter>,
			);

			// Check for flex centering classes
			const centerContainer = container.querySelector(".flex.items-center.justify-center");
			expect(centerContainer).toBeInTheDocument();
		});

		it("displays heading with appropriate size", () => {
			globalThis.mockRouteError = {
				status: 500,
				statusText: "Server Error",
				data: { message: "Something went wrong" },
			};

			render(
				<MemoryRouter>
					<ErrorPage />
				</MemoryRouter>,
			);

			const heading = screen.getByRole("heading");
			expect(heading).toBeInTheDocument();
			expect(heading).toHaveClass("text-4xl");
		});

		it("displays error message with appropriate text sizing", () => {
			globalThis.mockRouteError = "Critical error occurred";

			render(
				<MemoryRouter>
					<ErrorPage />
				</MemoryRouter>,
			);

			const message = screen.getByText("Critical error occurred");
			expect(message).toHaveClass("text-xl");
		});
	});
});
