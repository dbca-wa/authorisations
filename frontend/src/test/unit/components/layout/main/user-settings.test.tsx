import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { UserSettings } from '../../../../../components/layout/main/UserSettings';

describe('UserSettings page', () => {
    it('renders the under-construction page', () => {
        render(<UserSettings />);

        expect(screen.getByText("We're building something great here!")).toBeInTheDocument();
        expect(screen.getByText("Settings are still under construction. Check back soon.")).toBeInTheDocument();
    });
});
