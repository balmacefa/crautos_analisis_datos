"use client"
import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Search, 
  ArrowLeft, 
  Filter, 
  BarChart3, 
  TrendingUp, 
  MapPin, 
  Calendar, 
  Gauge,
  X,
  ChevronDown,
  ExternalLink,
  PieChart,
  LayoutGrid,
  Zap,
  DollarSign,
  Maximize2
} from 'lucide-react';
import Link from 'next/link';
import useSWR from 'swr';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs) {
  return twMerge(clsx(inputs));
}

const fetcher = (url) => fetch(url).then((res) => res.json());

// --- Custom Premium Components ---

const StatCard = ({ title, value, subtitle, icon: Icon, color = "blue" }) => (
  <motion.div 
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    className="glass p-6 rounded-[2rem] border border-white/10 flex flex-col gap-4 group hover:border-white/20 transition-all"
  >
    <div className="flex justify-between items-start">
      <div className={cn(
        "w-12 h-12 rounded-2xl flex items-center justify-center transition-transform group-hover:scale-110 duration-500",
        color === "blue" ? "bg-blue-600/20 text-blue-400" : 
        color === "green" ? "bg-emerald-600/20 text-emerald-400" : 
        "bg-indigo-600/20 text-indigo-400"
      )}>
        <Icon size={24} />
      </div>
    </div>
    <div>
      <p className="text-[10px] font-black uppercase tracking-[0.2em] text-white/30 mb-1">{title}</p>
      <h3 className="text-3xl font-black italic tracking-tighter leading-none">{value}</h3>
      <p className="text-xs text-white/40 mt-2 font-medium">{subtitle}</p>
    </div>
  </motion.div>
);

const DistributionBar = ({ label, count, total, color = "bg-blue-500", onClick, active }) => {
  const percentage = total > 0 ? (count / total) * 100 : 0;
  
  return (
    <div 
      onClick={onClick}
      className={cn(
        "group cursor-pointer py-1.5 px-3 rounded-xl transition-all",
        active ? "bg-white/10" : "hover:bg-white/5"
      )}
    >
      <div className="flex justify-between items-end mb-1.5">
        <span className={cn(
          "text-[11px] font-black uppercase tracking-wider transition-colors",
          active ? "text-white" : "text-white/40 group-hover:text-white/60"
        )}>
          {label}
        </span>
        <span className="text-[10px] font-mono text-white/20 font-bold">{count.toLocaleString()}</span>
      </div>
      <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
        <motion.div 
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 1, ease: [0.22, 1, 0.36, 1] }}
          className={cn("h-full rounded-full transition-colors", active ? color : "bg-white/20")}
        />
      </div>
    </div>
  );
};

export default function DynamicExplorer() {
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState({
    brands: '',
    year_min: '',
    year_max: '',
    price_min: '',
    price_max: '',
    provinces: '',
    fuels: '',
    transmissions: '',
    sort_by: 'año:desc'
  });

  // Debounce search query
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(searchQuery), 500);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Construct URL for V2 API with Faceting
  const queryUrl = useMemo(() => {
    const params = new URLSearchParams({
      q: debouncedQuery || '*',
      page: page.toString(),
      limit: '24',
      sort_by: filters.sort_by,
      facet_by: 'marca,año,combustible,transmisión,provincia'
    });

    if (filters.brands) params.append('brands', filters.brands);
    if (filters.year_min) params.append('year_min', filters.year_min);
    if (filters.year_max) params.append('year_max', filters.year_max);
    if (filters.price_min) params.append('price_min', filters.price_min);
    if (filters.price_max) params.append('price_max', filters.price_max);
    if (filters.provinces) params.append('provinces', filters.provinces);
    if (filters.fuels) params.append('fuels', filters.fuels);
    if (filters.transmissions) params.append('transmissions', filters.transmissions);

    return `http://localhost:8000/api/v2/cars?${params.toString()}`;
  }, [debouncedQuery, filters, page]);

  const { data, isLoading, error } = useSWR(queryUrl, fetcher, {
    keepPreviousData: true,
    revalidateOnFocus: false
  });

  const facets = data?.facets || [];
  const cars = data?.cars || [];
  const totalFound = data?.total || 0;

  const getFacet = (name) => facets.find(f => f.field_name === name)?.counts || [];

  const toggleFilter = (key, value) => {
    setFilters(prev => {
      const current = prev[key];
      if (current === value) return { ...prev, [key]: '' };
      return { ...prev, [key]: value };
    });
    setPage(1);
  };

  return (
    <main className="min-h-screen w-full gradient-bg font-sans pb-20 selection:bg-blue-500/30">
      {/* Dynamic Background */}
      <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden">
        <div className="absolute top-[-10%] right-[-10%] w-[60%] h-[60%] bg-blue-600/10 rounded-full blur-[120px] animate-pulse-slow" />
        <div className="absolute bottom-[-10%] left-[-10%] w-[60%] h-[60%] bg-indigo-600/10 rounded-full blur-[120px] animate-pulse-slow delay-1000" />
      </div>

      {/* Navigation Header */}
      <header className="sticky top-0 z-50 glass border-b border-white/5 backdrop-blur-3xl">
        <div className="max-w-[1800px] mx-auto px-6 h-20 flex items-center justify-between gap-8">
          <div className="flex items-center gap-6 shrink-0">
             <Link href="/" className="group p-3 bg-white/5 hover:bg-white/10 rounded-2xl transition-all border border-white/5">
                <ArrowLeft size={20} className="group-hover:-translate-x-1 transition-transform" />
             </Link>
             <div>
               <h1 className="text-2xl font-black italic tracking-tighter leading-none">
                 MARKET<span className="text-blue-500">EXPLORER</span>
               </h1>
               <div className="flex items-center gap-2 mt-1">
                 <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                 <p className="text-[9px] font-black uppercase tracking-widest text-white/40">Real-time Data Active</p>
               </div>
             </div>
          </div>

          <div className="flex-1 max-w-2xl relative group hidden md:block">
            <Search className="absolute left-5 top-1/2 -translate-y-1/2 text-white/20 group-focus-within:text-blue-500 transition-colors" size={20} />
            <input 
              type="text"
              placeholder="Explora por marca, modelo o año..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-[1.5rem] py-4 pl-14 pr-6 focus:outline-none focus:ring-2 focus:ring-blue-500/30 transition-all font-medium placeholder:text-white/20"
            />
          </div>

          <div className="flex items-center gap-4 shrink-0">
            <div className="hidden lg:flex flex-col items-end">
              <p className="text-[10px] font-black text-white/20 uppercase tracking-widest">Unidades Encontradas</p>
              <p className="text-xl font-mono font-black text-white leading-none">{totalFound.toLocaleString()}</p>
            </div>
            <button className="p-3 bg-blue-600 text-white rounded-2xl shadow-xl shadow-blue-900/20 hover:scale-105 transition-all">
              <LayoutGrid size={24} />
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-[1800px] mx-auto px-6 py-10 grid grid-cols-1 lg:grid-cols-[320px_1fr] gap-10 relative z-10">
        
        {/* Sidebar Facets */}
        <aside className="space-y-10 lg:sticky lg:top-32 h-fit">
          
          {/* Active Filters Summary */}
          {(filters.brands || filters.fuels || filters.transmissions || filters.provinces) && (
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <h3 className="text-[10px] font-black uppercase tracking-widest text-white/30">Filtros Activos</h3>
                <button 
                  onClick={() => setFilters({brands:'', year_min:'', year_max:'', price_min:'', price_max:'', provinces:'', fuels:'', transmissions:'', sort_by:'año:desc'})}
                  className="text-[10px] font-bold text-blue-400 hover:underline"
                >
                  Limpiar todo
                </button>
              </div>
              <div className="flex flex-wrap gap-2">
                {Object.entries(filters).map(([key, val]) => {
                  if (!val || key === 'sort_by' || key.includes('_')) return null;
                  return (
                    <button 
                      key={key}
                      onClick={() => toggleFilter(key, val)}
                      className="px-3 py-1.5 bg-blue-600/20 border border-blue-500/30 rounded-full text-[10px] font-bold flex items-center gap-2 group"
                    >
                      {val}
                      <X size={10} className="text-blue-400 group-hover:text-white" />
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Facet: Marca */}
          <section className="space-y-5">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-xl bg-blue-600/20 flex items-center justify-center text-blue-400">
                <BarChart3 size={16} />
              </div>
              <h3 className="text-xs font-black uppercase tracking-[0.2em]">Marcas Populares</h3>
            </div>
            <div className="space-y-1 max-h-[300px] overflow-y-auto pr-2 custom-scrollbar">
              {getFacet('marca').map((f) => (
                <DistributionBar 
                  key={f.value} 
                  label={f.value} 
                  count={f.count} 
                  total={totalFound} 
                  active={filters.brands === f.value}
                  onClick={() => toggleFilter('brands', f.value)}
                />
              ))}
            </div>
          </section>

          {/* Facet: Combustible */}
          <section className="space-y-5">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-xl bg-emerald-600/20 flex items-center justify-center text-emerald-400">
                <Zap size={16} />
              </div>
              <h3 className="text-xs font-black uppercase tracking-[0.2em]">Por Combustible</h3>
            </div>
            <div className="space-y-1">
              {getFacet('combustible').map((f) => (
                <DistributionBar 
                  key={f.value} 
                  label={f.value} 
                  count={f.count} 
                  total={totalFound} 
                  color="bg-emerald-500"
                  active={filters.fuels === f.value}
                  onClick={() => toggleFilter('fuels', f.value)}
                />
              ))}
            </div>
          </section>

          {/* Facet: Transmision */}
          <section className="space-y-5">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-xl bg-indigo-600/20 flex items-center justify-center text-indigo-400">
                <PieChart size={16} />
              </div>
              <h3 className="text-xs font-black uppercase tracking-[0.2em]">Transmisión</h3>
            </div>
            <div className="space-y-1">
              {getFacet('transmisión').map((f) => (
                <DistributionBar 
                  key={f.value} 
                  label={f.value} 
                  count={f.count} 
                  total={totalFound} 
                  color="bg-indigo-500"
                  active={filters.transmissions === f.value}
                  onClick={() => toggleFilter('transmissions', f.value)}
                />
              ))}
            </div>
          </section>

          {/* Facet: Provincia */}
          <section className="space-y-5">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-xl bg-amber-600/20 flex items-center justify-center text-amber-400">
                <MapPin size={16} />
              </div>
              <h3 className="text-xs font-black uppercase tracking-[0.2em]">Provincia</h3>
            </div>
            <div className="space-y-1">
              {getFacet('provincia').map((f) => (
                <DistributionBar 
                  key={f.value} 
                  label={f.value} 
                  count={f.count} 
                  total={totalFound} 
                  color="bg-amber-500"
                  active={filters.provinces === f.value}
                  onClick={() => toggleFilter('provinces', f.value)}
                />
              ))}
            </div>
          </section>
        </aside>

        {/* Dashboard Content */}
        <div className="space-y-12">
          
          {/* Hero Statistics */}
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            <StatCard 
              title="Precio Promedio" 
              value={`$${(cars.reduce((acc, c) => acc + (c.precio_usd || 0), 0) / (cars.length || 1)).toLocaleString(undefined, { maximumFractionDigits: 0 })}`}
              subtitle="Basado en los resultados actuales"
              icon={DollarSign}
              color="green"
            />
            <StatCard 
              title="Kilometraje Promedio" 
              value={`${(cars.reduce((acc, c) => acc + (c.informacion_general?.kilometraje_number || 0), 0) / (cars.length || 1)).toLocaleString(undefined, { maximumFractionDigits: 0 })} KM`}
              subtitle="Estado de uso del mercado"
              icon={Gauge}
              color="indigo"
            />
             <StatCard 
              title="Antigüedad Promedio" 
              value={`${Math.round(new Date().getFullYear() - (cars.reduce((acc, c) => acc + (c.año || 0), 0) / (cars.length || 1)))} Años`}
              subtitle="Modelo de año promedio"
              icon={Calendar}
              color="blue"
            />
          </div>

          <div className="flex items-center justify-between border-b border-white/5 pb-6">
            <div className="flex gap-8">
               <button className="text-sm font-black italic tracking-tighter text-blue-500 border-b-2 border-blue-500 pb-4">
                 Grid View
               </button>
               <button className="text-sm font-black italic tracking-tighter text-white/30 hover:text-white transition-colors pb-4">
                 Market Trends
               </button>
            </div>
            
            <div className="flex items-center gap-4">
              <p className="text-[10px] font-black text-white/30 uppercase tracking-widest hidden sm:block">Ordenar por</p>
              <select 
                value={filters.sort_by}
                onChange={(e) => setFilters(prev => ({...prev, sort_by: e.target.value}))}
                className="bg-white/5 border border-white/10 rounded-xl px-4 py-2 text-xs font-bold focus:outline-none focus:ring-1 focus:ring-blue-500"
              >
                <option value="año:desc" className="bg-zinc-900">Más Recientes</option>
                <option value="precio_usd:asc" className="bg-zinc-900">Precio: Menor a Mayor</option>
                <option value="precio_usd:desc" className="bg-zinc-900">Precio: Mayor a Menor</option>
                <option value="kilometraje_number:asc" className="bg-zinc-900">Menor Recorrido</option>
              </select>
            </div>
          </div>

          {/* Results Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-6 min-h-[600px]">
            <AnimatePresence>
              {isLoading ? (
                Array.from({ length: 9 }).map((_, i) => (
                  <div key={`skeleton-${i}`} className="glass rounded-[2rem] aspect-square animate-pulse border border-white/5 opacity-40" />
                ))
              ) : (
                cars.map((car) => (
                  <motion.div
                    key={car.car_id}
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.9 }}
                    transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
                    className="group relative glass rounded-[2rem] overflow-hidden border border-white/5 hover:border-blue-500/50 hover:shadow-[0_0_40px_rgba(59,130,246,0.1)] transition-all flex flex-col"
                  >
                    <div className="aspect-[16/10] relative overflow-hidden bg-white/[0.02] flex items-center justify-center">
                       {car.imagen_principal ? (
                         <img 
                          src={car.imagen_principal} 
                          alt={car.modelo} 
                          className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700"
                         />
                       ) : (
                         <TrendingUp className="text-white/5" size={80} />
                       )}
                       <div className="absolute top-4 right-4 px-3 py-1 bg-black/60 backdrop-blur-md rounded-full border border-white/10 text-[10px] font-black italic text-blue-400">
                        {car.año}
                       </div>
                    </div>

                    <div className="p-7 space-y-5 flex-1 flex flex-col">
                      <div>
                        <p className="text-[10px] font-black text-blue-500 uppercase tracking-widest mb-1">{car.marca}</p>
                        <h3 className="text-xl font-black italic tracking-tighter leading-none group-hover:text-blue-400 transition-colors truncate">
                          {car.modelo}
                        </h3>
                      </div>

                      <div className="grid grid-cols-2 gap-4 py-4 border-y border-white/5">
                        <div className="flex items-center gap-2">
                          <Gauge size={14} className="text-blue-500" />
                          <span className="text-[10px] font-black uppercase text-white/40">{car.informacion_general?.kilometraje_number?.toLocaleString() || 0} KM</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <MapPin size={14} className="text-blue-500" />
                          <span className="text-[10px] font-black uppercase text-white/40 truncate">{car.informacion_general?.provincia || 'N/A'}</span>
                        </div>
                      </div>

                      <div className="flex items-end justify-between mt-auto">
                         <div>
                            <p className="text-[9px] font-black text-white/20 uppercase tracking-[0.2em] mb-1">Precio Actual</p>
                            <p className="text-3xl font-mono font-black text-white tracking-tighter italic">
                              ${car.precio_usd?.toLocaleString()}
                            </p>
                         </div>
                         <a 
                          href={car.url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="w-12 h-12 rounded-2xl bg-white/5 hover:bg-blue-600 flex items-center justify-center transition-all group/btn"
                         >
                           <ExternalLink size={18} className="group-hover/btn:scale-110 transition-transform" />
                         </a>
                      </div>
                    </div>
                  </motion.div>
                ))
              )}
            </AnimatePresence>
          </div>

          {/* Pagination Placeholder */}
          {!isLoading && totalFound > cars.length && (
            <div className="pt-10 flex justify-center">
               <button 
                onClick={() => setPage(p => p + 1)}
                className="px-10 py-5 glass border border-white/10 rounded-[1.5rem] font-black italic uppercase text-xs tracking-widest hover:bg-white/5 transition-all group"
               >
                 Cargar más resultados <span className="text-blue-500 ml-2">→</span>
               </button>
            </div>
          )}

        </div>
      </div>
    </main>
  );
}
