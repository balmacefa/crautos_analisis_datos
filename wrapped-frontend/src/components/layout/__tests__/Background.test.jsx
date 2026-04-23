import { render, screen } from '@testing-library/react';
import { Background } from '../Background';

vi.mock('@/context/ThemeContext', () => ({
  useTheme: vi.fn(),
}));

import { useTheme } from '@/context/ThemeContext';

// Mock framer-motion to avoid animation issues in tests
vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, className, ...props }) => {
      // Omit framer-motion specific props that could interfere
      const { animate, transition, ...rest } = props;
      return <div className={className} data-testid="motion-div" {...rest}>{children}</div>;
    }
  }
}));

describe('Background', () => {
  it('renders correctly with dark theme', () => {
    useTheme.mockReturnValue({ theme: 'dark' });
    render(<Background />);
    const gridDiv = document.querySelector('.opacity-\\[0\\.03\\]');
    expect(gridDiv).toBeInTheDocument();
    expect(gridDiv).toHaveClass('invert-0');
  });

  it('renders correctly with light theme', () => {
    useTheme.mockReturnValue({ theme: 'light' });
    render(<Background />);
    const gridDiv = document.querySelector('.opacity-\\[0\\.03\\]');
    expect(gridDiv).toBeInTheDocument();
    expect(gridDiv).toHaveClass('invert');
  });
});
