import { render, screen } from '@testing-library/react';
import CarCardV2 from '../CarCardV2'; // Note: Default export

// Mock framer-motion to avoid animation issues in tests
vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, className, ...props }) => {
      // Omit framer-motion specific props that could interfere
      const { initial, animate, whileHover, whileTap, ...rest } = props;
      return <div className={className} data-testid="motion-div" {...rest}>{children}</div>;
    }
  }
}));

const mockCar = {
  marca: 'Toyota',
  modelo: 'Corolla',
  año: '2020',
  precio_usd: 15000,
  transmisión: 'Automática',
  combustible: 'Gasolina',
  kilometraje: '50,000 km',
  url: 'https://example.com/car',
  informacion_general: {
    provincia: 'San José'
  }
};

describe('CarCardV2', () => {
  it('renders correctly with all data', () => {
    render(<CarCardV2 car={mockCar} />);

    // Check main texts
    expect(screen.getAllByText('Toyota').length).toBeGreaterThan(0);
    expect(screen.getByText('Corolla')).toBeInTheDocument();
    expect(screen.getByText('2020')).toBeInTheDocument();
    expect(screen.getByText('Automática')).toBeInTheDocument();
    expect(screen.getByText('San José')).toBeInTheDocument();
    expect(screen.getByText('Gasolina')).toBeInTheDocument();
    expect(screen.getByText('50,000 km')).toBeInTheDocument();
    expect(screen.getByText('$15,000')).toBeInTheDocument();

    // Check link
    const link = screen.getByRole('link');
    expect(link).toHaveAttribute('href', 'https://example.com/car');
  });

  it('renders correctly with missing optional data', () => {
    const incompleteCar = {
      marca: 'Honda',
      modelo: 'Civic',
      año: '2018',
      precio_usd: null,
      url: 'https://example.com/honda',
    };

    render(<CarCardV2 car={incompleteCar} />);

    // Default province
    expect(screen.getByText('Costa Rica')).toBeInTheDocument();

    // N/A or defaults for missing stuff
    expect(screen.getByText('N/A')).toBeInTheDocument();
    expect(screen.getByText('Consultar')).toBeInTheDocument();
    expect(screen.getByText('$---')).toBeInTheDocument();
  });
});
