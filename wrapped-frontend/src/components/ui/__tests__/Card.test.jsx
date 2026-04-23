import { render, screen } from '@testing-library/react';
import { Card } from '../Card';

// Mock framer-motion to avoid animation issues in tests
vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, className, ...props }) => {
      // Omit framer-motion specific props that could interfere
      const { initial, whileInView, viewport, transition, whileHover, ...rest } = props;
      return <div className={className} data-testid="motion-div" {...rest}>{children}</div>;
    }
  }
}));

describe('Card', () => {
  it('renders correctly with default props', () => {
    render(<Card>Card Content</Card>);
    const card = screen.getByTestId('motion-div');
    expect(card).toBeInTheDocument();
    expect(card).toHaveTextContent('Card Content');
    expect(card).toHaveClass('bg-white/5');
  });

  it('renders dark variant correctly', () => {
    render(<Card variant="dark">Dark Card</Card>);
    const card = screen.getByTestId('motion-div');
    expect(card).toHaveClass('bg-black/40');
  });

  it('renders white variant correctly', () => {
    render(<Card variant="white">White Card</Card>);
    const card = screen.getByTestId('motion-div');
    expect(card).toHaveClass('bg-white');
  });

  it('adds custom className', () => {
    render(<Card className="custom-class">Custom</Card>);
    const card = screen.getByTestId('motion-div');
    expect(card).toHaveClass('custom-class');
  });
});
