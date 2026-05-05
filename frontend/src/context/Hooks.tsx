import { useEffect, useRef, useState } from 'react';


/**
 * Resolves a deferred promise from a route loader into component state.
 *
 * Data-agnostic: the hook does not know or care whether it is handling
 * applications, questionnaires, or any other resource type. The calling
 * component owns the type and the initial (empty) value.
 *
 * Returns a [resolvedValue, isLoading] tuple that mirrors the useState
 * pair it replaces, so call-sites stay readable and minimal.
 */
export const useResolvedPromise = <T,>(
	promise: Promise<T> | undefined,
	initialValue: T,
): [T, boolean] => {
	// Capture the initial value in a ref so it never causes the effect to
	// re-run when the caller passes an inline literal (e.g. [] or {}).
	const initialValueRef = useRef<T>(initialValue);
	const [value, setValue] = useState<T>(initialValue);
	// Start as loading only when a promise is actually provided, avoiding a
	// spurious loading flash on routes that omit this data.
	const [isLoading, setIsLoading] = useState<boolean>(promise !== undefined);

	useEffect(() => {
		if (!promise) {
			setIsLoading(false);
			return;
		}

		// Guard flag: prevents state updates if the component unmounts before the promise settles.
		let isMounted = true;
		setIsLoading(true);

		promise
			.then((resolved) => {
				if (!isMounted) return;
				setValue(resolved);
			})
			.catch(() => {
				// Fall back to the initial value so the empty-state UI can render safely.
				if (!isMounted) return;
				setValue(initialValueRef.current);
			})
			.finally(() => {
				if (!isMounted) return;
				setIsLoading(false);
			});

		return () => {
			isMounted = false;
		};
	}, [promise]);

	return [value, isLoading];
};
