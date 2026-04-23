import { render, screen } from '@testing-library/react';
import { BottomNav } from '../BottomNav';
import { ThemeProvider } from '@/context/ThemeContext';
import { usePathname } from 'next/navigation';
import { useTheme } from '@/context/ThemeContext';

vi.mock('@/context/ThemeContext', () => ({
  useTheme: vi.fn(),
}));

vi.mock('next/navigation', () => ({
  usePathname: vi.fn(),
}));

// Mock Link from next/link
vi.mock('next/link', () => {
  return {
    default: ({ href, children, className }) => {
      return (
        <a href={href} className={className} data-testid={`link-${href}`}>
          {children}
        </a>
      );
    },
  };
});

describe('BottomNav', () => {
  it('renders correctly and highlights Inicio tab', () => {
    useTheme.mockReturnValue({ theme: 'dark' });
    usePathname.mockReturnValue('/');
    render(<BottomNav />);

    expect(screen.getByText('Inicio')).toBeInTheDocument();

    const navItem = screen.getByTestId('link-/');
    expect(navItem).toHaveClass('text-cyan-500');

    const otherItem = screen.getByTestId('link-/tour');
    expect(otherItem).toHaveClass('text-slate-500');
  });

  it('highlights Tour tab correctly', () => {
    useTheme.mockReturnValue({ theme: 'dark' });
    usePathname.mockReturnValue('/tour');
    render(<BottomNav />);

    const navItem = screen.getByTestId('link-/tour');
    expect(navItem).toHaveClass('text-cyan-500');
  });

  it('highlights Explorer tab correctly', () => {
    useTheme.mockReturnValue({ theme: 'dark' });
    usePathname.mockReturnValue('/search');
    render(<BottomNav />);

    const navItem = screen.getByTestId('link-/search');
    expect(navItem).toHaveClass('text-cyan-500');
  });

  it('highlights Insights tab correctly', () => {
    useTheme.mockReturnValue({ theme: 'dark' });
    usePathname.mockReturnValue('/insights');
    render(<BottomNav />);

    const navItem = screen.getByTestId('link-/insights');
    expect(navItem).toHaveClass('text-cyan-500');
  });

  it('handles unknown path correctly', () => {
    useTheme.mockReturnValue({ theme: 'dark' });
    usePathname.mockReturnValue('/unknown');
    render(<BottomNav />);

    const navItem = screen.getByTestId('link-/');
    expect(navItem).toHaveClass('text-slate-500');
  });

  it('applies light theme styling correctly', () => {
    useTheme.mockReturnValue({ theme: 'light' });
    usePathname.mockReturnValue('/');
    render(<BottomNav />);

    const nav = document.querySelector('nav');
    expect(nav).toHaveClass('bg-white/90');
  });
});
