import { useContext, useEffect, useRef, useState } from 'react';
import { DialogContext, type DialogContextType } from './DialogContext';
import { SnackbarContext, type SnackbarContextType } from './SnackbarContext';


/**
 * Returns the shared dialog context API and enforces provider usage.
 */
export const useDialog = (): DialogContextType => {
	const context = useContext(DialogContext);
	if (!context) {
		throw new Error('useDialog must be used within a DialogProvider');
	}
	return context;
};


/**
 * Returns the shared snackbar context API and enforces provider usage.
 */
export const useSnackbar = (): SnackbarContextType => {
	const context = useContext(SnackbarContext);
	if (!context) {
		throw new Error('useSnackbar must be used within a SnackbarProvider');
	}
	return context;
};


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
	// Track which promise has settled so loading can be derived without
	// mutating state synchronously inside the effect body.
	const [settledPromise, setSettledPromise] = useState<Promise<T> | undefined>(undefined);

	useEffect(() => {
		if (!promise) {
			return;
		}

		// Guard flag: prevents state updates if the component unmounts before the promise settles.
		let isMounted = true;

		promise
			.then((resolved) => {
				if (!isMounted) return;
				setValue(resolved);
				setSettledPromise(promise);
			})
			.catch(() => {
				// Fall back to the initial value so the empty-state UI can render safely.
				if (!isMounted) return;
				setValue(initialValueRef.current);
				setSettledPromise(promise);
			});

		return () => {
			isMounted = false;
		};
	}, [promise]);

	const isLoading = promise !== undefined && settledPromise !== promise;

	return [value, isLoading];
};
