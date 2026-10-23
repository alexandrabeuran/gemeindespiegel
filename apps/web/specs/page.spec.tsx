import { render, screen } from '@testing-library/react';
import HomePage from '../src/app/page';

describe('HomePage', () => {
  it('shows the project name as heading', () => {
    render(<HomePage />);
    const heading = screen.getByRole('heading', { name: 'Gemeindespiegel' });
    expect(heading).toBeTruthy();
  });
});
