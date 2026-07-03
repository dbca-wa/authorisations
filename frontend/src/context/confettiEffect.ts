import confetti from 'canvas-confetti';

/**
 * Fires a confetti sequence with customizable parameters and repetition count.
 *
 * @param celebrate Number of successive confetti bursts to fire (default: 3).
 * @param particleCount Base number of particles per burst (default: 90).
 * @param spread Spread angle in degrees (default: 120).
 */
export const fireConfettiEffect = (
    celebrate: number = 3,
    particleCount: number = 90,
    spread: number = 120,
) => {
    for (let i = 0; i < celebrate; i++) {
        window.setTimeout(() => {
            const adjustedParticleCount = Math.round(particleCount * Math.max(0.2, 1 - (i / celebrate) * 0.8));
            const adjustedSpread = spread * (1 + (i / celebrate) * 0.5);

            confetti({
                particleCount: adjustedParticleCount,
                spread: adjustedSpread,
                startVelocity: 60,
                origin: { y: 0.85 },
                zIndex: 2500,
            });
        }, i * 250);
    }
};
