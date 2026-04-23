import { render, screen } from '@testing-library/react';
import { Select } from '../Select';
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

describe('Select', () => {
  it('renders correctly in dark theme', () => {
    useTheme.mockReturnValue({ theme: 'dark' });
    render(
      <Select data-testid="select">
        <option>Option 1</option>
      </Select>
    );
    const select = screen.getByTestId('select');
    expect(select).toBeInTheDocument();
    expect(select).toHaveClass('bg-white/5');
  });

  it('renders correctly in light theme', () => {
    useTheme.mockReturnValue({ theme: 'light' });
    render(
      <Select data-testid="select">
        <option>Option 1</option>
      </Select>
    );
    const select = screen.getByTestId('select');
    expect(select).toHaveClass('bg-slate-50');
  });

  it('adds custom className', () => {
    useTheme.mockReturnValue({ theme: 'dark' });
    render(
      <Select data-testid="select" className="custom-select">
        <option>Option 1</option>
      </Select>
    );
    const select = screen.getByTestId('select');
    expect(select).toHaveClass('custom-select');
  });

  it('passes other props correctly', () => {
    useTheme.mockReturnValue({ theme: 'dark' });
    render(
      <Select data-testid="select" required disabled>
        <option>Option 1</option>
      </Select>
    );
    const select = screen.getByTestId('select');
    expect(select).toBeRequired();
    expect(select).toBeDisabled();
  });
});
