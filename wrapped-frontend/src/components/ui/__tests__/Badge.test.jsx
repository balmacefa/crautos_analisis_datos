import { render, screen } from '@testing-library/react';
import { Badge } from '../Badge';

describe('Badge', () => {
  it('renders correctly with default variant', () => {
    render(<Badge>Default</Badge>);
    const badge = screen.getByText('Default');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass('bg-cyan-500/20');
  });

  it('renders correctly with purple variant', () => {
    render(<Badge variant="purple">Purple</Badge>);
    const badge = screen.getByText('Purple');
    expect(badge).toHaveClass('bg-purple-500/20');
  });

  it('renders correctly with amber variant', () => {
    render(<Badge variant="amber">Amber</Badge>);
    const badge = screen.getByText('Amber');
    expect(badge).toHaveClass('bg-amber-500/20');
  });

  it('renders correctly with emerald variant', () => {
    render(<Badge variant="emerald">Emerald</Badge>);
    const badge = screen.getByText('Emerald');
    expect(badge).toHaveClass('bg-emerald-500/20');
  });

  it('renders correctly with rose variant', () => {
    render(<Badge variant="rose">Rose</Badge>);
    const badge = screen.getByText('Rose');
    expect(badge).toHaveClass('bg-rose-500/20');
  });

  it('adds custom className', () => {
    render(<Badge className="custom-class">Custom</Badge>);
    const badge = screen.getByText('Custom');
    expect(badge).toHaveClass('custom-class');
  });
});
