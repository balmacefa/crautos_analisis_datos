import { render, screen, fireEvent } from '@testing-library/react';
import CarCardV2 from '../CarCardV2';

vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, className, ...props }) => {
      const { initial, animate, whileHover, whileTap, ...rest } = props;
      return <div className={className} data-testid="motion-div" {...rest}>{children}</div>;
    }
  }
}));

const baseCar = {
  marca: 'Toyota',
  modelo: 'Corolla',
  año: '2020',
  precio_usd: 15000,
};

describe('CarCardV2', () => {
  it('renders correctly with all data', () => {
    const car = { ...baseCar, combustible: 'Gasolina', kilometraje: '50,000 km', url: 'https://example.com' };
    render(<CarCardV2 car={car} />);
    expect(screen.getByText('Corolla')).toBeInTheDocument();
  });

  it('prioritizes imagen_principal when available', () => {
    const car = {
      ...baseCar,
      informacion_general: {
        imagen_principal: 'https://example.com/main.jpg',
        imagenes_secundarias: ['https://example.com/sec1.jpg', 'https://example.com/sec2.jpg']
      }
    };
    render(<CarCardV2 car={car} />);
    const img = screen.getByRole('img');
    expect(img).toHaveAttribute('src', 'https://example.com/main.jpg');
    expect(img).toHaveAttribute('alt', 'Toyota Corolla');
  });

  it('falls back to the first item in imagenes_secundarias if imagen_principal is missing', () => {
    const car = {
      ...baseCar,
      informacion_general: {
        imagenes_secundarias: ['https://example.com/sec1.jpg', 'https://example.com/sec2.jpg']
      }
    };
    render(<CarCardV2 car={car} />);
    const img = screen.getByRole('img');
    expect(img).toHaveAttribute('src', 'https://example.com/sec1.jpg');
  });

  it('uses generic image if no images are provided', () => {
    const car = { ...baseCar };
    render(<CarCardV2 car={car} />);
    const img = screen.getByRole('img');
    expect(img).toHaveAttribute('src', '/images/car-placeholder.png');
  });

  it('uses fallback image when onError is triggered', () => {
    const car = {
      ...baseCar,
      informacion_general: {
        imagen_principal: 'https://example.com/broken.jpg',
      }
    };
    render(<CarCardV2 car={car} />);
    const img = screen.getByRole('img');
    fireEvent.error(img);
    expect(img.src).toContain('/images/car-placeholder.png');
  });
});
