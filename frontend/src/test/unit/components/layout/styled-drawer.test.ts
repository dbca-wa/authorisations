import { createTheme } from '@mui/material/styles';
import { describe, it, expect } from 'vitest';
import { openDrawerOffsetMixin } from '../../../../components/layout/StyledDrawer';

describe('StyledDrawer', () => {
    const theme = createTheme();

    describe('openDrawerOffsetMixin', () => {
        it('returns correct base drawer offset values', () => {
            const offset = openDrawerOffsetMixin(theme);
            
            expect(offset.marginLeft).toBe(240);
            expect(offset.width).toBe('calc(100% - 240px)');
        });

        it('includes responsive breakpoint for lg', () => {
            const offset = openDrawerOffsetMixin(theme);
            const lgBreakpoint = offset[theme.breakpoints.up('lg')] as Record<string, unknown>;
            
            expect(lgBreakpoint).toBeDefined();
            expect(lgBreakpoint.marginLeft).toBe(280);
            expect(lgBreakpoint.width).toBe('calc(100% - 280px)');
        });

        it('includes responsive breakpoint for xl', () => {
            const offset = openDrawerOffsetMixin(theme);
            const xlBreakpoint = offset[theme.breakpoints.up('xl')] as Record<string, unknown>;
            
            expect(xlBreakpoint).toBeDefined();
            expect(xlBreakpoint.marginLeft).toBe(320);
            expect(xlBreakpoint.width).toBe('calc(100% - 320px)');
        });

        it('maintains width consistency with drawerWidths configuration', () => {
            const offset = openDrawerOffsetMixin(theme);
            const lgBreakpoint = offset[theme.breakpoints.up('lg')] as Record<string, unknown>;
            const xlBreakpoint = offset[theme.breakpoints.up('xl')] as Record<string, unknown>;
            
            // Base widths should be consistent across all breakpoints
            expect(offset.marginLeft).toBeLessThanOrEqual(320);
            expect(lgBreakpoint.marginLeft).toBeLessThanOrEqual(320);
            expect(xlBreakpoint.marginLeft).toBe(320);
        });
    });
});
