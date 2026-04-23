import { render, screen, fireEvent } from '@testing-library/react';
import { Header } from '../Header';
import { ThemeProvider } from '@/context/ThemeContext';
import { useTheme } from '@/context/ThemeContext';

vi.mock('@/context/ThemeContext', () => ({
  useTheme: vi.fn(),
}));

// Mock framer-motion to avoid animation issues in tests
vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, className, ...props }) => {
      // Omit framer-motion specific props that could interfere
      const { whileHover, ...rest } = props;
      return <div className={className} data-testid="motion-div" {...rest}>{children}</div>;
    },
    h1: ({ children, className, ...props }) => {
      // Omit framer-motion specific props that could interfere
      const { initial, animate, transition, ...rest } = props;
      return <h1 className={className} data-testid="motion-h1" {...rest}>{children}</h1>;
    }
  }
}));

describe('Header', () => {
  it('renders correctly in dark theme', () => {
    const toggleThemeMock = vi.fn();
    useTheme.mockReturnValue({ theme: 'dark', toggleTheme: toggleThemeMock });
    render(<Header />);

    expect(screen.getByText(/EL FUTURO DEL/)).toBeInTheDocument();

    const h1 = screen.getByTestId('motion-h1');
    expect(h1).toHaveClass('text-white');

    const span = screen.getByText('ANÁLISIS AUTOMOTRIZ');
    expect(span).toHaveClass('bg-clip-text');
  });

  it('renders correctly in light theme', () => {
    const toggleThemeMock = vi.fn();
    useTheme.mockReturnValue({ theme: 'light', toggleTheme: toggleThemeMock });
    render(<Header />);

    const h1 = screen.getByTestId('motion-h1');
    expect(h1).toHaveClass('text-slate-900');

    const span = screen.getByText('ANÁLISIS AUTOMOTRIZ');
    expect(span).toHaveClass('text-cyan-600');
  });

  it('calls toggleTheme on button click', () => {
    const toggleThemeMock = vi.fn();
    useTheme.mockReturnValue({ theme: 'dark', toggleTheme: toggleThemeMock });
    render(<Header />);

    const button = screen.getByRole('button');
    fireEvent.click(button);
    expect(toggleThemeMock).toHaveBeenCalledTimes(1);
  });

  it('adds custom className', () => {
    const toggleThemeMock = vi.fn();
    useTheme.mockReturnValue({ theme: 'dark', toggleTheme: toggleThemeMock });
    render(<Header className="custom-header" />);

    const header = document.querySelector('header');
    expect(header).toHaveClass('custom-header');
  });
});
