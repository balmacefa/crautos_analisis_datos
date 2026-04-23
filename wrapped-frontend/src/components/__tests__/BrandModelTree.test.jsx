import { render, screen, fireEvent } from '@testing-library/react';
import { BrandModelTree } from '../BrandModelTree';

const mockData = [
  { marca: 'Toyota', modelo: 'Corolla', count: 100 },
  { marca: 'Toyota', modelo: 'Yaris', count: 50 },
  { marca: 'Honda', modelo: 'Civic', count: 80 },
  { marca: 'Ford', modelo: 'Mustang', count: 20 },
];

describe('BrandModelTree', () => {
  it('renders correctly and builds the tree', () => {
    render(<BrandModelTree data={mockData} />);

    // Check if brands are rendered
    expect(screen.getByText('Toyota')).toBeInTheDocument();
    expect(screen.getByText('Honda')).toBeInTheDocument();
    expect(screen.getByText('Ford')).toBeInTheDocument();

    // Check if totals are calculated (Toyota: 150)
    expect(screen.getByText('150')).toBeInTheDocument();
  });

  it('expands brand on click and shows models', () => {
    render(<BrandModelTree data={mockData} />);

    const toyotaRow = screen.getByText('Toyota').closest('div').parentElement;
    fireEvent.click(toyotaRow);

    expect(screen.getByText('Corolla')).toBeInTheDocument();
    expect(screen.getByText('Yaris')).toBeInTheDocument();
  });

  it('filters tree by search term', () => {
    render(<BrandModelTree data={mockData} />);

    const input = screen.getByPlaceholderText('Filtrar marcas o modelos...');
    fireEvent.change(input, { target: { value: 'yaris' } });

    // Toyota should be visible because Yaris is inside it
    expect(screen.getByText('Toyota')).toBeInTheDocument();
    expect(screen.getByText('Yaris')).toBeInTheDocument();

    // Honda and Ford should be filtered out
    expect(screen.queryByText('Honda')).not.toBeInTheDocument();
    expect(screen.queryByText('Ford')).not.toBeInTheDocument();
  });

  it('calls onSelectBrand when brand checkbox is clicked', () => {
    const onSelectBrand = vi.fn();
    render(<BrandModelTree data={mockData} onSelectBrand={onSelectBrand} />);

    const checkboxWrapper = screen.getByText('Toyota').previousElementSibling;
    fireEvent.click(checkboxWrapper);

    expect(onSelectBrand).toHaveBeenCalledWith('Toyota');
  });

  it('calls onSelectModel when model is clicked', () => {
    const onSelectModel = vi.fn();
    render(<BrandModelTree data={mockData} onSelectModel={onSelectModel} />);

    // Expand Toyota
    const toyotaRow = screen.getByText('Toyota').closest('div').parentElement;
    fireEvent.click(toyotaRow);

    const corollaRow = screen.getByText('Corolla');
    fireEvent.click(corollaRow);

    expect(onSelectModel).toHaveBeenCalledWith('Corolla');
  });

  it('applies selected styles to brands and models', () => {
    render(
      <BrandModelTree
        data={mockData}
        selectedBrands={['Toyota']}
        selectedModels={['Corolla']}
      />
    );

    // Expand Toyota to see Corolla
    const toyotaRow = screen.getByText('Toyota').closest('div').parentElement;
    fireEvent.click(toyotaRow);

    // Since it's selected, it should have the CheckSquare (represented by cyan text)
    expect(screen.getByText('Toyota')).toHaveClass('text-cyan-400');
    expect(screen.getByText('Corolla').parentElement).toHaveClass('bg-white/10 text-cyan-400');
  });
});
