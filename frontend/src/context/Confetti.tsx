import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

import { useCallback, useEffect, useMemo, useState } from 'react';
import confetti from 'canvas-confetti';
import { debounce } from 'underscore';

/**
 * Number of rapid clicks required to trigger the confetti effect.
 * Set to 10 to create a satisfying "easter egg" discovery experience—low enough to find quickly,
 * high enough to prevent accidental triggers during normal usage.
 */
const CLICK_TARGET = 10;

/**
 * Time window (in milliseconds) within which all CLICK_TARGET clicks must occur to trigger confetti.
 * Set to 1800ms (1.8 seconds) to define "rapid" clicks—allows a natural clicking rhythm while still
 * requiring deliberate, focused interaction. If the user pauses longer, the click count resets.
 */
const WINDOW_MS = 1800;

/**
 * Fires a confetti sequence with customizable parameters and repetition count.
 *
 * @param celebrate - Number of successive confetti bursts to fire (default: 3).
 * @param particleCount - Base number of particles per burst (default: 90).
 * @param spread - Spread angle in degrees (default: 120).
 *   Particle count decreases with each burst (cascading effect from 100% down to 20% minimum).
 *   Spread increases with each burst (expanding from original up to 150%) for a widening celebration.
 *   Bursts are staggered 250ms apart to create visual rhythm. Example: celebrate=10 fires 10 bursts over 2.25 seconds.
 */
export const fireConfettiEffect = (celebrate: number = 3, particleCount: number = 90, spread: number = 120) => {
    for (let i = 0; i < celebrate; i++) {
        window.setTimeout(() => {
            // Reduce particles with each burst for a fading cascade effect.
            const adjustedParticleCount = Math.round(particleCount * Math.max(0.2, 1 - (i / celebrate) * 0.8));
            // Increase spread with each burst to create expanding celebration effect.
            const adjustedSpread = spread * (1 + (i / celebrate) * 0.5);

            confetti({
                particleCount: adjustedParticleCount,
                spread: adjustedSpread,
                startVelocity: 45,
                origin: { y: 0.85 },
                zIndex: 2500,
            });
        }, i * 250);
    }
};

/**
 * Renders an interactive element that triggers a confetti effect after rapid repeated clicks.
 * The short-time burst window is enforced with underscore debounce to keep trigger timing predictable.
 */
export const Confetti = ({
    children,
    celebrate,
    particleCount,
    spread,
}: {
    children: React.ReactNode;
    celebrate?: number;
    particleCount?: number;
    spread?: number;
}) => {
    const [_burstClickCount, setBurstClickCount] = useState<number>(0);
    const [activationCount, setActivationCount] = useState<number>(0);

    /**
     * Reset the burst if the user pauses too long between clicks.
     */
    const resetBurstCounter = useMemo(
        () => debounce(() => {
            setBurstClickCount(0);
        }, WINDOW_MS),
        [],
    );

    /**
     * Cancels pending debounce callbacks when the component unmounts.
     * This prevents delayed state updates after navigation.
     */
    useEffect(() => {
        return () => {
            resetBurstCounter.cancel();
        };
    }, [resetBurstCounter]);

    /**
     * Skip if no trigger has fired yet; ensures confetti only plays after successful click burst.
     */
    useEffect(() => {
        if (activationCount === 0) {
            return;
        }

        // Respect user accessibility preferences: do not animate if the browser/OS has motion reduction enabled.
        // window.matchMedia() queries CSS media features; 'prefers-reduced-motion: reduce' is set by
        // users in OS accessibility settings or browser settings to avoid motion-triggered discomfort.
        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            return;
        }

        // Trigger the confetti effect with the configured particle count, spread, and celebration count.
        fireConfettiEffect(celebrate, particleCount, spread);
    }, [activationCount, particleCount, spread, celebrate]);

    /**
     * Tracks clicks and triggers the confetti effect on the target count.
     * It intentionally resets burst tracking immediately after activation to support repeated triggers.
     */
    const handleClick = useCallback(() => {
        setBurstClickCount((previousCount) => {
            const nextCount = previousCount + 1;

            if (nextCount >= CLICK_TARGET) {
                resetBurstCounter.cancel();
                setActivationCount((previousActivationCount) => previousActivationCount + 1);
                return 0;
            }

            resetBurstCounter();
            return nextCount;
        });
    }, [resetBurstCounter]);

    return (
        <Box
            sx={{ px: 2, mb: 8, textAlign: 'center' }}
            role="button"
            tabIndex={0}
            onClick={handleClick}
            onKeyDown={(event) => {
                if (event.key === 'Enter' || event.key === ' ') {
                    event.preventDefault();
                    handleClick();
                }
            }}
            aria-label="Confetti trigger"
        >
            <Typography variant="caption" sx={{ color: 'text.disabled', cursor: 'inherit', userSelect: 'none' }}>
                {children}
            </Typography>
        </Box>
    );
};