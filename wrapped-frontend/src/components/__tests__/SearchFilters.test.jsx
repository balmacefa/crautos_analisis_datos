import { render, screen, fireEvent, act } from '@testing-library/react';
import SearchFilters from '../SearchFilters'; // Default export

describe('SearchFilters', () => {
  const defaultFilters = {
    q: '',
    brands: [],
    year_min: 1990,
    year_max: 2025,
    price_max: 150000,
    km_max: 300000
  };

  const mockBrands = [
    { marca: 'Toyota' },
    { marca: 'Honda' },
    { marca: 'Nissan' }
  ];

  it('renders all filter sections', () => {
    const setFilters = vi.fn();
    const onClear = vi.fn();

    render(
      <SearchFilters
        filters={defaultFilters}
        setFilters={setFilters}
        brands={mockBrands}
        models={[]}
        onClear={onClear}
      />
    );

    expect(screen.getByText('Búsqueda Libre')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Toyota, 4x4, etc.')).toBeInTheDocument();

    expect(screen.getByText('Marcas')).toBeInTheDocument();
    expect(screen.getByText('Toyota')).toBeInTheDocument();
    expect(screen.getByText('Honda')).toBeInTheDocument();

    expect(screen.getByText('Rango de Año')).toBeInTheDocument();
    expect(screen.getByText('Precio Máximo (USD)')).toBeInTheDocument();
    expect(screen.getByText('Kilometraje Máximo (km)')).toBeInTheDocument();

    expect(screen.getByText('Restablecer Filtros')).toBeInTheDocument();
  });

  it('calls setFilters on query change', async () => {
    // In order to properly test the setState updater with e.target.value
    // we use a real state mock mechanism or just test the component itself with userEvent/fireEvent and a wrapper
    let currentFilters = defaultFilters;
    const setFilters = vi.fn((updater) => {
      if (typeof updater === 'function') {
        currentFilters = updater(currentFilters);
      } else {
        currentFilters = updater;
      }
    });

    const { rerender } = render(
      <SearchFilters
        filters={currentFilters}
        setFilters={setFilters}
        brands={mockBrands}
        onClear={vi.fn()}
      />
    );

    const input = screen.getByPlaceholderText('Toyota, 4x4, etc.');

    await act(async () => {
      fireEvent.change(input, { target: { value: 'Corolla' } });
    });

    expect(setFilters).toHaveBeenCalledTimes(1);
    expect(currentFilters.q).toBe('Corolla');
  });

  it('calls setFilters on brand toggle', () => {
    const setFilters = vi.fn();

    render(
      <SearchFilters
        filters={defaultFilters}
        setFilters={setFilters}
        brands={mockBrands}
        onClear={vi.fn()}
      />
    );

    const toyotaButton = screen.getByText('Toyota');
    fireEvent.click(toyotaButton);

    expect(setFilters).toHaveBeenCalledTimes(1);

    const updater = setFilters.mock.calls[0][0];
    const newFilters = updater(defaultFilters);
    expect(newFilters.brands).toEqual(['Toyota']);
  });

  it('toggles brand off if already selected', () => {
    const setFilters = vi.fn();
    const filtersWithBrand = { ...defaultFilters, brands: ['Toyota'] };

    render(
      <SearchFilters
        filters={filtersWithBrand}
        setFilters={setFilters}
        brands={mockBrands}
        onClear={vi.fn()}
      />
    );

    const toyotaButton = screen.getByText('Toyota');
    expect(toyotaButton).toHaveClass('bg-blue-600');

    fireEvent.click(toyotaButton);

    const updater = setFilters.mock.calls[0][0];
    const newFilters = updater(filtersWithBrand);
    expect(newFilters.brands).toEqual([]);
  });

  it('calls onClear when clear button is clicked', () => {
    const onClear = vi.fn();

    render(
      <SearchFilters
        filters={defaultFilters}
        setFilters={vi.fn()}
        brands={mockBrands}
        onClear={onClear}
      />
    );

    const clearBtn = screen.getByText('Restablecer Filtros');
    fireEvent.click(clearBtn);

    expect(onClear).toHaveBeenCalledTimes(1);
  });

  it('clears brands when Limpiar is clicked', () => {
    const setFilters = vi.fn();
    const filtersWithBrand = { ...defaultFilters, brands: ['Toyota', 'Honda'] };

    render(
      <SearchFilters
        filters={filtersWithBrand}
        setFilters={setFilters}
        brands={mockBrands}
        onClear={vi.fn()}
      />
    );

    const limpiarBtn = screen.getByText('Limpiar');
    fireEvent.click(limpiarBtn);

    const updater = setFilters.mock.calls[0][0];
    const newFilters = updater(filtersWithBrand);
    expect(newFilters.brands).toEqual([]);
  });

  it('calls setFilters on range slider change', () => {
    const setFilters = vi.fn();

    render(
      <SearchFilters
        filters={defaultFilters}
        setFilters={setFilters}
        brands={mockBrands}
        onClear={vi.fn()}
      />
    );

    // Get the first range input (Year max)
    const sliders = document.querySelectorAll('input[type="range"]');
    expect(sliders.length).toBe(3);

    const yearMaxSlider = sliders[0];
    fireEvent.change(yearMaxSlider, { target: { value: '2020' } });

    expect(setFilters).toHaveBeenCalledTimes(1);

    const updater = setFilters.mock.calls[0][0];
    const newFilters = updater(defaultFilters);
    expect(newFilters.year_max).toBe(2020);
  });
});
