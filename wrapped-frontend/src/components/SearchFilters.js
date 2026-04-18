"use client"
import React from 'react';
import { Search, X, Filter, ChevronDown } from 'lucide-react';

export default function SearchFilters({ 
  filters, 
  setFilters, 
  brands, 
  models, 
  onClear 
}) {
  return (
    <div className="space-y-8">
      {/* Search Input */}
      <div className="space-y-3">
        <label className="text-[10px] font-bold text-white/40 uppercase tracking-[2px]">Búsqueda Libre</label>
        <div className="relative group">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-white/20 group-focus-within:text-blue-400 transition-colors" size={18} />
          <input 
            type="text"
            placeholder="Toyota, 4x4, etc."
            value={filters.q}
            onChange={(e) => setFilters(prev => ({ ...prev, q: e.target.value }))}
            className="w-full bg-white/5 border border-white/10 rounded-2xl py-3.5 pl-12 pr-4 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all placeholder:text-white/20"
          />
        </div>
      </div>

      {/* Brand Selection */}
      <div className="space-y-3">
        <div className="flex justify-between items-center">
          <label className="text-[10px] font-bold text-white/40 uppercase tracking-[2px]">Marcas</label>
          <button 
            onClick={() => setFilters(prev => ({ ...prev, brands: [] }))}
            className="text-[10px] font-bold text-blue-400 hover:text-blue-300 transition-colors uppercase"
          >
            Limpiar
          </button>
        </div>
        <div className="grid grid-cols-2 gap-2 max-h-40 overflow-y-auto pr-2 custom-scrollbar">
          {brands.map(b => (
            <button
              key={b.marca}
              onClick={() => {
                const newBrands = filters.brands.includes(b.marca)
                  ? filters.brands.filter(x => x !== b.marca)
                  : [...filters.brands, b.marca];
                setFilters(prev => ({ ...prev, brands: newBrands }));
              }}
              className={`text-xs p-2.5 rounded-xl border transition-all text-left ${
                filters.brands.includes(b.marca) 
                  ? "bg-blue-600 border-blue-400 text-white font-bold" 
                  : "bg-white/5 border-white/10 text-white/60 hover:bg-white/10"
              }`}
            >
              {b.marca}
            </button>
          ))}
        </div>
      </div>

      {/* Year Slider */}
      <RangeFilter 
        label="Rango de Año"
        min={1990}
        max={2025}
        values={[filters.year_min, filters.year_max]}
        onChange={(min, max) => setFilters(prev => ({ ...prev, year_min: min, year_max: max }))}
      />

      {/* Price Slider */}
      <RangeFilter 
        label="Precio Máximo (USD)"
        min={0}
        max={150000}
        step={5000}
        single={true}
        values={[0, filters.price_max]}
        onChange={(_, max) => setFilters(prev => ({ ...prev, price_max: max }))}
        format={(v) => `$${(v/1000)}k`}
      />

      {/* Mileage Slider */}
      <RangeFilter 
        label="Kilometraje Máximo (km)"
        min={0}
        max={300000}
        step={10000}
        single={true}
        values={[0, filters.km_max]}
        onChange={(_, max) => setFilters(prev => ({ ...prev, km_max: max }))}
        format={(v) => `${(v/1000)}k km`}
      />

      <button 
        onClick={onClear}
        className="w-full py-4 bg-white/5 hover:bg-red-500/10 border border-white/10 hover:border-red-500/30 text-white/60 hover:text-red-400 rounded-2xl transition-all font-bold text-sm flex items-center justify-center gap-2 group"
      >
        <X size={16} className="group-hover:rotate-90 transition-transform" />
        Restablecer Filtros
      </button>
    </div>
  );
}

function RangeFilter({ label, min, max, step = 1, values, onChange, single = false, format = (v) => v }) {
  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <label className="text-[10px] font-bold text-white/40 uppercase tracking-[2px]">{label}</label>
        <span className="text-xs font-mono font-bold text-blue-400">
          {single ? format(values[1]) : `${format(values[0])} - ${format(values[1])}`}
        </span>
      </div>
      <input 
        type="range"
        min={min}
        max={max}
        step={step}
        value={values[1]}
        onChange={(e) => onChange(values[0], parseInt(e.target.value))}
        className="w-full h-1.5 bg-white/10 rounded-lg appearance-none cursor-pointer accent-blue-500"
      />
    </div>
  );
}
