import React from 'react';
import { cn } from '@/lib/utils';
import { Card } from '@/components/ui/Card';
import { Select } from '@/components/ui/Select';
import { BrandModelTree } from '@/components/BrandModelTree';
import { TrendingUp, Grid, List as ListIcon, ShieldCheck } from 'lucide-react';

export function SearchSidebar({
  filters,
  setFilters,
  viewMode,
  setViewMode,
  facets,
  allModels,
  provinces,
  fuels
}) {
  return (
    <div className="space-y-8">
      <Card className="p-6 space-y-6" hover={false}>
        <h3 className="text-sm font-black uppercase tracking-widest flex items-center gap-2">
          <TrendingUp size={16} className="text-cyan-400" />
          Parámetros
        </h3>

        <div className="space-y-6">
          {/* Brand/Model Selection */}
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <label className="text-[10px] font-black text-white/40 uppercase tracking-widest">Vehículo</label>
              <div className="flex bg-white/5 rounded-lg p-0.5 border border-white/10">
                <button
                  onClick={() => setViewMode('list')}
                  className={cn(
                    "p-1.5 rounded-md transition-all",
                    viewMode === 'list' ? "bg-cyan-600 text-white shadow-lg" : "text-white/40 hover:text-white"
                  )}
                >
                  <Grid size={12} />
                </button>
                <button
                  onClick={() => setViewMode('tree')}
                  className={cn(
                    "p-1.5 rounded-md transition-all",
                    viewMode === 'tree' ? "bg-cyan-600 text-white shadow-lg" : "text-white/40 hover:text-white"
                  )}
                >
                  <ListIcon size={12} />
                </button>
              </div>
            </div>

            {viewMode === 'list' ? (
              <div className="grid grid-cols-2 gap-2 max-h-48 overflow-y-auto pr-2 custom-scrollbar">
                {facets.marca?.map(b => (
                  <button
                    key={b.value}
                    onClick={() => {
                      const current = filters.brands ? filters.brands.split(',') : [];
                      const next = current.includes(b.value)
                        ? current.filter(x => x !== b.value)
                        : [...current, b.value];
                      setFilters(prev => ({ ...prev, brands: next.join(','), models: "" }));
                    }}
                    className={cn(
                      "text-[10px] p-2 rounded-xl border transition-all text-left font-bold truncate",
                      filters.brands?.split(',').includes(b.value)
                        ? "bg-cyan-600 border-cyan-400 text-white"
                        : "bg-white/5 border-white/10 text-white/40 hover:text-white hover:bg-white/10"
                    )}
                  >
                    {b.value}
                  </button>
                ))}
              </div>
            ) : (
              <BrandModelTree
                data={allModels}
                selectedBrands={filters.brands ? filters.brands.split(',') : []}
                selectedModels={filters.models ? filters.models.split(',') : []}
                onSelectBrand={(brand) => {
                  const current = filters.brands ? filters.brands.split(',') : [];
                  const next = current.includes(brand)
                    ? current.filter(x => x !== brand)
                    : [...current, brand];
                  setFilters(prev => ({ ...prev, brands: next.join(',') }));
                }}
                onSelectModel={(model) => {
                  const current = filters.models ? filters.models.split(',') : [];
                  const next = current.includes(model)
                    ? current.filter(x => x !== model)
                    : [...current, model];
                  setFilters(prev => ({ ...prev, models: next.join(',') }));
                }}
              />
            )}
          </div>

          {/* Price Range */}
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <label className="text-[10px] font-black text-white/40 uppercase tracking-widest">
                Rango de Precio ({filters.price_currency})
              </label>
              <div className="flex bg-white/5 rounded-lg p-0.5 border border-white/10">
                <button
                  onClick={() => setFilters(p => ({...p, price_currency: 'CRC', price_min: "", price_max: ""}))}
                  className={cn(
                    "text-[9px] font-bold px-2 py-1 rounded-md transition-all",
                    filters.price_currency === 'CRC' ? "bg-emerald-600 text-white shadow-lg" : "text-white/40 hover:text-white"
                  )}
                >
                  CRC
                </button>
                <button
                  onClick={() => setFilters(p => ({...p, price_currency: 'USD', price_min: "", price_max: ""}))}
                  className={cn(
                    "text-[9px] font-bold px-2 py-1 rounded-md transition-all",
                    filters.price_currency === 'USD' ? "bg-emerald-600 text-white shadow-lg" : "text-white/40 hover:text-white"
                  )}
                >
                  USD
                </button>
              </div>
            </div>

            <div className="flex gap-2">
              <Select
                value={filters.price_min}
                onChange={e => setFilters(p => ({...p, price_min: e.target.value}))}
                className="h-10 text-xs w-full"
              >
                <option value="">Min</option>
                {filters.price_currency === 'CRC' ? (
                  <>
                    <option value="2000000">₡2M</option>
                    <option value="5000000">₡5M</option>
                    <option value="10000000">₡10M</option>
                    <option value="15000000">₡15M</option>
                    <option value="20000000">₡20M</option>
                    <option value="30000000">₡30M</option>
                  </>
                ) : (
                  <>
                    <option value="5000">$5k</option>
                    <option value="10000">$10k</option>
                    <option value="15000">$15k</option>
                    <option value="20000">$20k</option>
                    <option value="30000">$30k</option>
                    <option value="50000">$50k</option>
                  </>
                )}
              </Select>

              <Select
                value={filters.price_max}
                onChange={e => setFilters(p => ({...p, price_max: e.target.value}))}
                className="h-10 text-xs w-full"
              >
                <option value="">Max</option>
                {filters.price_currency === 'CRC' ? (
                  <>
                    <option value="5000000">₡5M</option>
                    <option value="10000000">₡10M</option>
                    <option value="15000000">₡15M</option>
                    <option value="20000000">₡20M</option>
                    <option value="30000000">₡30M</option>
                    <option value="50000000">₡50M</option>
                  </>
                ) : (
                  <>
                    <option value="10000">$10k</option>
                    <option value="15000">$15k</option>
                    <option value="20000">$20k</option>
                    <option value="30000">$30k</option>
                    <option value="50000">$50k</option>
                    <option value="100000">$100k</option>
                  </>
                )}
              </Select>
            </div>
          </div>

          {/* Years Range */}
          <div className="space-y-3">
            <label className="text-[10px] font-black text-white/40 uppercase tracking-widest">Años</label>
            <Select
              value={filters.year_min === filters.year_max && filters.year_min ? filters.year_min : ""}
              onChange={e => {
                const val = e.target.value;
                if (!val) {
                  setFilters(p => ({ ...p, year_min: "", year_max: "" }));
                } else {
                  setFilters(p => ({ ...p, year_min: val, year_max: val }));
                }
              }}
              className="h-10 text-xs w-full"
            >
              <option value="">Todos los años</option>
              {(facets.año || [])
                .sort((a, b) => parseInt(b.value) - parseInt(a.value))
                .map(y => (
                  <option key={y.value} value={y.value}>{y.value} ({y.count})</option>
                ))
              }
            </Select>
          </div>

          {/* Provinces */}
          <div className="space-y-3">
            <label className="text-[10px] font-black text-white/40 uppercase tracking-widest">Provincia</label>
            <Select value={filters.provincias} onChange={e => setFilters(p => ({...p, provinces: e.target.value}))} className="h-10">
              <option value="">Todas las provincias</option>
              {provinces.map(p => (
                <option key={p.provincia} value={p.provincia}>{p.provincia}</option>
              ))}
            </Select>
          </div>

          {/* Fuel Types */}
          <div className="space-y-3">
            <label className="text-[10px] font-black text-white/40 uppercase tracking-widest">Combustible</label>
            <div className="flex flex-wrap gap-2">
              {fuels.map((f) => (
                <button
                  key={f.combustible}
                  onClick={() => setFilters((p) => ({ ...p, fuels: p.fuels === f.combustible ? "" : f.combustible }))}
                  className={cn(
                    "px-3 py-1.5 rounded-lg text-[10px] font-bold uppercase transition-all border",
                    filters.fuels === f.combustible
                      ? "bg-cyan-600 border-cyan-400 text-white"
                      : "bg-white/5 border-white/5 text-white/40 hover:text-white",
                  )}
                >
                  {f.combustible}
                </button>
              ))}
            </div>
          </div>

          {/* Sort By */}
          <div className="space-y-3">
            <label className="text-[10px] font-black text-white/40 uppercase tracking-widest">Ordenar por</label>
            <Select value={filters.sort_by} onChange={e => setFilters(p => ({...p, sort_by: e.target.value}))} className="h-10">
              <option value="año:desc">Más Recientes</option>
              <option value="precio_usd:asc">Menor Precio</option>
              <option value="precio_usd:desc">Mayor Precio</option>
              <option value="kilometraje_number:asc">Menor Kilometraje</option>
            </Select>
          </div>

          {/* Data Sources */}
          <div className="space-y-3">
            <label className="text-[10px] font-black text-white/40 uppercase tracking-widest">Fuente de Datos</label>
            <div className="grid grid-cols-2 gap-2">
              {(facets.fuente || []).map(f => (
                <button
                  key={f.value}
                  onClick={() => {
                    const current = filters.fuentes ? filters.fuentes.split(',') : [];
                    const next = current.includes(f.value)
                      ? current.filter(x => x !== f.value)
                      : [...current, f.value];
                    setFilters(p => ({ ...p, fuentes: next.join(',') }));
                  }}
                  className={cn(
                    "text-[10px] p-2 rounded-xl border transition-all text-left font-bold truncate flex justify-between items-center",
                    filters.fuentes?.split(',').includes(f.value)
                      ? "bg-cyan-600 border-cyan-400 text-white"
                      : "bg-white/5 border-white/10 text-white/40 hover:text-white hover:bg-white/10"
                  )}
                >
                  <span>{f.value}</span>
                  <span className="opacity-50 text-[9px]">{f.count}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      </Card>

      <Card className="p-6 bg-cyan-600/10 border-cyan-500/20" hover={false}>
         <div className="flex items-center gap-2 text-cyan-400 font-black text-[10px] uppercase tracking-widest">
            <ShieldCheck size={14} /> Sugerencia IA
         </div>
         <p className="text-xs text-white/60 leading-relaxed italic mt-4">
           "Recuerda que los autos con menos de 80,000km suelen tener mejor valor de reventa en Costa Rica."
         </p>
      </Card>
    </div>
  );
}
