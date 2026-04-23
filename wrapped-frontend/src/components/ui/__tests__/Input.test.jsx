import { render, screen } from '@testing-library/react';
import { Input } from '../Input';
import { ThemeProvider } from '@/context/ThemeContext';

// Mock the ThemeContext useTheme hook
vi.mock('@/context/ThemeContext', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useTheme: vi.fn(),
  };
});

import { useTheme } from '@/context/ThemeContext';

describe('Input', () => {
  it('renders correctly in dark theme', () => {
    useTheme.mockReturnValue({ theme: 'dark' });
    render(<Input placeholder="Search..." />);
    const input = screen.getByPlaceholderText('Search...');
    expect(input).toBeInTheDocument();
    expect(input).toHaveClass('bg-white/5');
  });

  it('renders correctly in light theme', () => {
    useTheme.mockReturnValue({ theme: 'light' });
    render(<Input placeholder="Search..." />);
    const input = screen.getByPlaceholderText('Search...');
    expect(input).toHaveClass('bg-slate-50');
  });

  it('adds custom className', () => {
    useTheme.mockReturnValue({ theme: 'dark' });
    render(<Input placeholder="Search..." className="custom-input" />);
    const input = screen.getByPlaceholderText('Search...');
    expect(input).toHaveClass('custom-input');
  });

  it('passes other props correctly', () => {
    useTheme.mockReturnValue({ theme: 'dark' });
    render(<Input placeholder="Search..." type="password" required />);
    const input = screen.getByPlaceholderText('Search...');
    expect(input).toHaveAttribute('type', 'password');
    expect(input).toBeRequired();
  });
});
