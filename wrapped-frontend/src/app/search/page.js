"use client"
import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Search, 
  ArrowLeft, 
  Filter, 
  Car, 
  TrendingUp, 
  MapPin, 
  Calendar, 
  Gauge,
  X,
  ChevronDown,
  ExternalLink,
  ShieldCheck,
  Info,
  Layers,
  Check,
  ArrowRightLeft,
  Droplets,
  Zap,
  DollarSign
} from 'lucide-react';
import Link from 'next/link';
import useSWR from 'swr';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs) {
  return twMerge(clsx(inputs));
}

import { getApiBaseUrl, robustFetcher as fetcher } from '@/lib/api';

export default function SearchExplorer() {
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');
  const [extraCars, setExtraCars] = useState([]);
  const [page, setPage] = useState(1);
  const [showFilters, setShowFilters] = useState(false);
  const [selectedCar, setSelectedCar] = useState(null);
  const [comparisonList, setComparisonList] = useState([]);
  const [isComparing, setIsComparing] = useState(false);
  
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
    const timer = setTimeout(() => setDebouncedQuery(searchQuery), 400);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  const baseUrl = getApiBaseUrl();

  // SWR for filters data
  const { data: brandsData } = useSWR(`${baseUrl}/api/insights/brands`, fetcher);
  const { data: provincesData } = useSWR(`${baseUrl}/api/insights/provinces`, fetcher);
  const { data: fuelsData } = useSWR(`${baseUrl}/api/insights/distribution/fuel`, fetcher);
  const { data: transmissionsData } = useSWR(`${baseUrl}/api/insights/distribution/transmission`, fetcher);

  const brands = useMemo(() => brandsData?.slice(0, 30) || [], [brandsData]);
  const provinces = useMemo(() => provincesData || [], [provincesData]);
  const fuels = useMemo(() => fuelsData || [], [fuelsData]);
  const transmissions = useMemo(() => transmissionsData || [], [transmissionsData]);

  // Construct URL for V2 API
  const queryUrl = useMemo(() => {
    const params = new URLSearchParams({
      q: debouncedQuery || '*',
      page: '1',
      limit: '20',
      sort_by: filters.sort_by
    });

    if (filters.brands) params.append('brands', filters.brands);
    if (filters.year_min) params.append('year_min', filters.year_min);
    if (filters.year_max) params.append('year_max', filters.year_max);
    if (filters.price_min) params.append('price_min', filters.price_min);
    if (filters.price_max) params.append('price_max', filters.price_max);
    if (filters.provinces) params.append('provinces', filters.provinces);
    if (filters.fuels) params.append('fuels', filters.fuels);
    if (filters.transmissions) params.append('transmissions', filters.transmissions);

    return `${baseUrl}/api/v2/cars?${params.toString()}`;
  }, [debouncedQuery, filters]);

  const { data: initialData, isLoading: initialLoading } = useSWR(queryUrl, fetcher, {
    revalidateOnFocus: false,
    keepPreviousData: true
  });

  useEffect(() => {
    setExtraCars([]);
    setPage(1);
  }, [queryUrl]);

  const fetchMore = async () => {
    const nextPage = page + 1;
    let url = queryUrl.replace('page=1', `page=${nextPage}`);
    const data = await fetcher(url);
    if (data.cars) {
      setExtraCars(prev => [...prev, ...data.cars]);
      setPage(nextPage);
    }
  };

  const allCars = useMemo(() => {
    const initial = initialData?.cars || [];
    return [...initial, ...extraCars];
  }, [initialData, extraCars]);

  const total = initialData?.total || 0;

  const toggleComparison = (e, car) => {
    e.stopPropagation();
    setComparisonList(prev => {
      const exists = prev.find(c => c.car_id === car.car_id);
      if (exists) return prev.filter(c => c.car_id !== car.car_id);
      if (prev.length >= 3) return prev; // Limit to 3
      return [...prev, car];
    });
  };

  const isCarInComparison = (carId) => comparisonList.some(c => c.car_id === carId);

  return (
    <main className="min-h-screen w-full gradient-bg font-sans pb-20 relative">
      {/* Background kinetic elements from Wrapped for consistency */}
      <div className="absolute inset-0 z-0 opacity-10 pointer-events-none overflow-hidden">
        <div className="absolute top-[20%] left-[10%] w-64 h-64 bg-blue-600 rounded-full blur-[120px] animate-pulse-slow" />
        <div className="absolute bottom-[20%] right-[10%] w-64 h-64 bg-indigo-600 rounded-full blur-[120px] animate-pulse-slow delay-1000" />
      </div>

      {/* Header */}
      <header className="sticky top-0 z-40 glass border-b border-white/10 px-4 md:px-8 py-4 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row gap-4 items-center justify-between">
          <div className="flex items-center gap-4 w-full md:w-auto">
            <Link href="/" className="p-2 hover:bg-white/5 rounded-full transition-colors">
              <ArrowLeft size={24} />
            </Link>
            <div>
              <h2 className="text-xl font-black italic tracking-tighter leading-none">Crautos <span className="text-blue-400">Search</span></h2>
              <p className="text-[10px] text-white/40 uppercase font-black tracking-widest mt-1">Market Explorer v2</p>
            </div>
          </div>

          <div className="relative w-full md:max-w-md group">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-white/30 group-focus-within:text-blue-400 transition-colors" size={18} />
            <input 
              type="text" 
              placeholder="Busca por marca, modelo o año..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-2xl py-3.5 pl-12 pr-4 focus:outline-none focus:ring-2 focus:ring-blue-500/30 transition-all font-medium placeholder:text-white/20"
            />
          </div>

          <div className="flex items-center gap-3 w-full md:w-auto justify-end">
             <button 
              onClick={() => setShowFilters(!showFilters)}
              className={cn(
                "flex items-center gap-2 px-5 py-3 rounded-2xl border transition-all font-bold text-xs uppercase tracking-widest",
                showFilters ? "bg-blue-600 border-blue-400 text-white" : "bg-white/5 border-white/10 text-white/60 hover:text-white"
              )}
            >
              <Filter size={16} />
              Filtros
            </button>
          </div>
        </div>
      </header>

      {/* Sidebar & Grid Layout */}
      <div className="max-w-7xl mx-auto px-4 py-8 md:px-8 flex flex-col lg:flex-row gap-8">
        
        {/* Desktop Sidebar Filters */}
        <aside className="hidden lg:block w-72 shrink-0 space-y-8">
          <div className="glass-card p-6 rounded-3xl border border-white/5 space-y-6">
            <h3 className="text-sm font-black uppercase tracking-widest flex items-center gap-2">
              <TrendingUp size={16} className="text-blue-400" />
              Parámetros
            </h3>
            
            <div className="space-y-6">
              <div className="space-y-3">
                <label className="text-[10px] font-black text-white/40 uppercase tracking-widest">Rango de Precio (USD)</label>
                <div className="flex gap-2">
                   <input type="number" placeholder="Min" value={filters.price_min} onChange={e => setFilters(p => ({...p, price_min: e.target.value}))} className="w-full bg-white/5 border border-white/10 rounded-xl p-2 text-xs focus:ring-1 focus:ring-blue-500/50 outline-none" />
                   <input type="number" placeholder="Max" value={filters.price_max} onChange={e => setFilters(p => ({...p, price_max: e.target.value}))} className="w-full bg-white/5 border border-white/10 rounded-xl p-2 text-xs focus:ring-1 focus:ring-blue-500/50 outline-none" />
                </div>
              </div>

              <div className="space-y-3">
                <label className="text-[10px] font-black text-white/40 uppercase tracking-widest">Años</label>
                <div className="flex gap-2">
                   <input type="number" placeholder="Desde" value={filters.year_min} onChange={e => setFilters(p => ({...p, year_min: e.target.value}))} className="w-full bg-white/5 border border-white/10 rounded-xl p-2 text-xs focus:ring-1 focus:ring-blue-500/50 outline-none" />
                   <input type="number" placeholder="Hasta" value={filters.year_max} onChange={e => setFilters(p => ({...p, year_max: e.target.value}))} className="w-full bg-white/5 border border-white/10 rounded-xl p-2 text-xs focus:ring-1 focus:ring-blue-500/50 outline-none" />
                </div>
              </div>

              <div className="space-y-3">
                <label className="text-[10px] font-black text-white/40 uppercase tracking-widest">Provincia</label>
                <select 
                  value={filters.provincias} 
                  onChange={e => setFilters(p => ({...p, provinces: e.target.value}))}
                  className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-xs focus:ring-1 focus:ring-blue-500/50 outline-none appearance-none cursor-pointer"
                >
                  <option value="" className="bg-zinc-900">Todas las provincias</option>
                  {provinces.map(p => (
                    <option key={p.provincia} value={p.provincia} className="bg-zinc-900">{p.provincia}</option>
                  ))}
                </select>
              </div>

              <div className="space-y-3">
                <label className="text-[10px] font-black text-white/40 uppercase tracking-widest">Combustible</label>
                <div className="flex flex-wrap gap-2">
                  {fuels.map(f => (
                    <button
                      key={f.combustible}
                      onClick={() => setFilters(p => ({...p, fuels: p.fuels === f.combustible ? '' : f.combustible}))}
                      className={cn(
                        "px-3 py-1.5 rounded-lg text-[10px] font-bold uppercase transition-all border",
                        filters.fuels === f.combustible 
                          ? "bg-blue-600 border-blue-400 text-white" 
                          : "bg-white/5 border-white/5 text-white/40 hover:text-white"
                      )}
                    >
                      {f.combustible}
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-3">
                <label className="text-[10px] font-black text-white/40 uppercase tracking-widest">Transmisión</label>
                <div className="flex gap-2">
                  {transmissions.map(t => (
                    <button
                      key={t.transmisión}
                      onClick={() => setFilters(p => ({...p, transmissions: p.transmissions === t.transmisión ? '' : t.transmisión}))}
                      className={cn(
                        "flex-1 py-2 rounded-xl text-[10px] font-bold uppercase transition-all border",
                        filters.transmissions === t.transmisión 
                          ? "bg-indigo-600 border-indigo-400 text-white" 
                          : "bg-white/5 border-white/5 text-white/40 hover:text-white"
                      )}
                    >
                      {t.transmisión}
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-3">
                <label className="text-[10px] font-black text-white/40 uppercase tracking-widest">Ordenar por</label>
                <select 
                  value={filters.sort_by} 
                  onChange={e => setFilters(p => ({...p, sort_by: e.target.value}))}
                  className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-xs focus:ring-1 focus:ring-blue-500/50 outline-none appearance-none cursor-pointer"
                >
                  <option value="año:desc" className="bg-zinc-900">Más Recientes</option>
                  <option value="precio_usd:asc" className="bg-zinc-900">Menor Precio</option>
                  <option value="precio_usd:desc" className="bg-zinc-900">Mayor Precio</option>
                  <option value="kilometraje_number:asc" className="bg-zinc-900">Menor Kilometraje</option>
                </select>
              </div>
            </div>
          </div>

          <div className="p-6 bg-blue-600/10 border border-blue-500/20 rounded-3xl space-y-4">
             <div className="flex items-center gap-2 text-blue-400 font-black text-[10px] uppercase tracking-widest">
                <ShieldCheck size={14} /> Sugerencia IA
             </div>
             <p className="text-xs text-white/60 leading-relaxed italic">
               "Recuerda que los autos con menos de 80,000km suelen tener mejor valor de reventa en Costa Rica."
             </p>
          </div>
        </aside>

        {/* Main Content Area */}
        <div className="flex-1 space-y-8 z-10">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
            <div>
              <h1 className="text-4xl font-black italic tracking-tighter leading-none">
                {debouncedQuery ? `Resultados para "${debouncedQuery}"` : 'Explora el Mercado'}
              </h1>
              <p className="font-mono text-xs text-white/30 uppercase mt-4 tracking-tighter">
                Mostrando <span className="text-blue-400 font-bold">{allCars.length}</span> de {total.toLocaleString()} anuncios activos
              </p>
            </div>
          </div>

          {/* Results Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-2 xl:grid-cols-3 gap-6 min-h-[50vh]">
            {allCars.map((car, i) => (
              <motion.div 
                key={car.car_id + i}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: (i % 6) * 0.05 }}
                onClick={() => setSelectedCar(car)}
                className={cn(
                  "group relative glass rounded-3xl overflow-hidden border border-white/10 hover:border-blue-500/50 transition-all flex flex-col cursor-pointer",
                  isCarInComparison(car.car_id) && "ring-2 ring-blue-500 border-transparent shadow-[0_0_30px_rgba(59,130,246,0.3)]"
                )}
              >
                {/* Comparison Checkbox Overlay */}
                <button 
                  onClick={(e) => toggleComparison(e, car)}
                  className={cn(
                    "absolute top-4 left-4 z-20 w-8 h-8 rounded-xl border flex items-center justify-center transition-all",
                    isCarInComparison(car.car_id) 
                      ? "bg-blue-600 border-blue-400 text-white" 
                      : "bg-black/40 border-white/20 text-transparent group-hover:text-white/20"
                  )}
                >
                  <Check size={16} />
                </button>

                <div className="aspect-[16/10] bg-white/5 relative overflow-hidden flex items-center justify-center">
                  <Car className="text-white/10 group-hover:scale-110 transition-transform duration-700" size={80} />
                  <div className="absolute top-4 right-4 px-3 py-1 rounded-full glass border border-white/10 text-xs font-black italic text-blue-400">
                    {car.año}
                  </div>
                </div>

                <div className="p-6 flex-1 flex flex-col gap-5">
                  <div>
                    <h3 className="text-xs font-black text-blue-400 uppercase tracking-widest mb-1">{car.marca}</h3>
                    <p className="text-2xl font-black tracking-tighter leading-none truncate">{car.modelo}</p>
                  </div>

                  <div className="grid grid-cols-2 gap-4 py-4 border-y border-white/5">
                    <div className="flex items-center gap-2 text-white/50">
                      <Gauge size={14} className="text-blue-500" />
                      <span className="text-[11px] font-black uppercase truncate">{car.informacion_general?.kilometraje_number?.toLocaleString() || '0'} KM</span>
                    </div>
                    <div className="flex items-center gap-2 text-white/50">
                      <MapPin size={14} className="text-blue-500" />
                      <span className="text-[11px] font-black uppercase truncate">{car.informacion_general?.provincia || 'N/A'}</span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between mt-auto pt-2">
                    <div>
                      <p className="text-[10px] font-black text-white/20 uppercase tracking-widest">Precio Hoy</p>
                      <p className="text-3xl font-black font-mono text-green-400 tracking-tighter">
                        ${car.precio_usd?.toLocaleString()}
                      </p>
                    </div>
                    <div className="w-12 h-12 bg-white/5 group-hover:bg-blue-600 rounded-2xl flex items-center justify-center transition-all transform group-hover:rotate-45">
                      <ChevronDown className="text-white -rotate-90" size={20} />
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}

            {initialLoading && allCars.length === 0 && Array.from({ length: 6 }).map((_, i) => (
               <div key={i} className="glass rounded-3xl h-[400px] animate-pulse opacity-10" />
            ))}
          </div>

          {/* Empty State */}
          {!initialLoading && allCars.length === 0 && (
             <div className="text-center py-20 glass rounded-3xl border border-white/5">
                <Search size={64} className="mx-auto text-white/10 mb-4" />
                <h2 className="text-2xl font-bold">No encontramos lo que buscas</h2>
                <p className="text-white/40 mt-2">Prueba ajustando los filtros o cambiando la búsqueda.</p>
                <button 
                  onClick={() => {setSearchQuery(''); setFilters({brands:'', year_min:'', year_max:'', price_min:'', price_max:'', provinces:'', fuels:'', transmissions:'', sort_by:'año:desc'})}}
                  className="mt-6 px-6 py-3 bg-blue-600 rounded-xl font-bold text-sm"
                >
                  Limpiar filtros
                </button>
             </div>
          )}

          {/* Load More */}
          {allCars.length < total && !initialLoading && (
            <div className="mt-12 flex justify-center">
              <button 
                onClick={fetchMore}
                className="px-8 py-5 glass border border-white/10 rounded-2xl font-black uppercase text-xs tracking-[0.2em] hover:bg-white/5 transition-all text-white/40 hover:text-white"
              >
                Cargar más unidades
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Mobile Comparison Tray */}
      <AnimatePresence>
        {comparisonList.length > 0 && (
          <motion.div 
            initial={{ y: 100 }}
            animate={{ y: 0 }}
            exit={{ y: 100 }}
            className="fixed bottom-0 left-0 right-0 z-50 glass-header border-t border-white/10 px-6 py-4 backdrop-blur-2xl"
          >
            <div className="max-w-7xl mx-auto flex items-center justify-between gap-6">
              <div className="flex items-center gap-4 overflow-x-auto pb-2 scrollbar-none">
                <div className="flex -space-x-3">
                  {comparisonList.map((car, i) => (
                    <div key={car.car_id} className="w-12 h-12 rounded-2xl bg-blue-600 border-2 border-zinc-900 flex items-center justify-center shadow-xl">
                       <Car size={16} className="text-white" />
                    </div>
                  ))}
                  {Array.from({ length: 3 - comparisonList.length }).map((_, i) => (
                    <div key={i} className="w-12 h-12 rounded-2xl bg-white/5 border-2 border-zinc-900 border-dashed flex items-center justify-center" />
                  ))}
                </div>
                <div className="hidden sm:block">
                  <p className="text-sm font-black italic tracking-tighter">{comparisonList.length} / 3 vehículos seleccionados</p>
                  <p className="text-[10px] text-white/30 uppercase font-black">Máximo 3 para comparar</p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                 <button onClick={() => setComparisonList([])} className="p-4 rounded-2xl bg-white/5 hover:bg-white/10 text-white/40 transition-colors">
                    <X size={20} />
                 </button>
                 <button 
                  disabled={comparisonList.length < 2}
                  onClick={() => setIsComparing(true)}
                  className={cn(
                    "flex items-center gap-3 px-8 py-4 rounded-2xl font-black text-xs uppercase tracking-widest transition-all",
                    comparisonList.length >= 2 
                      ? "bg-blue-600 hover:bg-blue-500 shadow-xl shadow-blue-900/40 text-white animate-pulse" 
                      : "bg-white/5 text-white/20 cursor-not-allowed"
                  )}
                >
                  <ArrowRightLeft size={18} />
                  Comparar ahora
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Comparison Modal View */}
      <AnimatePresence>
        {isComparing && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[60] bg-black/95 backdrop-blur-2xl flex flex-col p-4 md:p-12 overflow-y-auto"
          >
            <div className="max-w-6xl mx-auto w-full space-y-12">
              <div className="flex justify-between items-center">
                <div>
                   <h2 className="text-4xl font-black italic tracking-tighter text-blue-400">Batalla de Titanes</h2>
                   <p className="text-white/40 uppercase font-black text-xs tracking-widest mt-2">Comparativa técnica lado a lado</p>
                </div>
                <button onClick={() => setIsComparing(false)} className="p-4 rounded-full bg-white/5 hover:bg-white/10 transition-colors">
                   <X size={24} />
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {comparisonList.map(car => (
                  <div key={car.car_id} className="glass rounded-3xl overflow-hidden border border-white/10 p-8 space-y-8 h-full bg-white/5">
                    <div className="text-center space-y-2">
                       <p className="text-xs font-black text-blue-400 uppercase tracking-widest">{car.marca}</p>
                       <h3 className="text-2xl font-black tracking-tighter leading-none italic">{car.modelo}</h3>
                       <p className="text-3xl font-mono font-black text-green-400 mt-4">${car.precio_usd?.toLocaleString()}</p>
                    </div>

                    <div className="space-y-6 pt-6 border-t border-white/10">
                       <div className="space-y-1">
                          <p className="text-[10px] text-white/30 uppercase font-black tracking-widest">Año</p>
                          <p className="font-bold text-lg">{car.año}</p>
                       </div>
                       <div className="space-y-1">
                          <p className="text-[10px] text-white/30 uppercase font-black tracking-widest">Recorrido</p>
                          <p className="font-bold text-lg">{car.informacion_general?.kilometraje_number?.toLocaleString()} KM</p>
                       </div>
                       <div className="space-y-1">
                          <p className="text-[10px] text-white/30 uppercase font-black tracking-widest">Combustible</p>
                          <p className="font-bold text-lg">{car.informacion_general?.combustible || 'N/A'}</p>
                       </div>
                       <div className="space-y-1">
                          <p className="text-[10px] text-white/30 uppercase font-black tracking-widest">Transmisión</p>
                          <p className="font-bold text-lg">{car.informacion_general?.transmisión || 'N/A'}</p>
                       </div>
                       <div className="space-y-1">
                          <p className="text-[10px] text-white/30 uppercase font-black tracking-widest">Provincia</p>
                          <p className="font-bold text-lg">{car.informacion_general?.provincia || 'N/A'}</p>
                       </div>
                    </div>

                    <a 
                      href={car.url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="w-full py-4 bg-white/5 hover:bg-blue-600 rounded-2xl flex items-center justify-center gap-2 font-black text-xs uppercase transition-all"
                    >
                      Ver en Crautos
                      <ExternalLink size={14} />
                    </a>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Details Modal (Selected Car) */}
      <AnimatePresence>
        {selectedCar && !isComparing && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md"
            onClick={() => setSelectedCar(null)}
          >
            <motion.div 
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.9, y: 20 }}
              onClick={e => e.stopPropagation()}
              className="w-full max-w-2xl bg-zinc-900 rounded-[2.5rem] border border-white/10 p-8 overflow-hidden relative"
            >
              <button 
                onClick={() => setSelectedCar(null)}
                className="absolute top-6 right-6 p-2 h-10 w-10 bg-white/5 hover:bg-white/10 rounded-full flex items-center justify-center transition-colors z-10"
              >
                <X size={20} />
              </button>

              <div className="flex flex-col gap-8">
                <div className="flex gap-6 items-start">
                   <div className="w-24 h-24 bg-blue-600/20 rounded-3xl flex items-center justify-center shrink-0 border border-blue-500/30">
                     <Car size={40} className="text-blue-400" />
                   </div>
                   <div className="flex-1">
                      <p className="text-blue-400 font-extrabold uppercase tracking-widest text-[10px] mb-1">{selectedCar.marca}</p>
                      <h2 className="text-4xl font-black italic tracking-tighter italic leading-[0.9]">{selectedCar.modelo}</h2>
                      <div className="flex gap-3 mt-4">
                         <span className="px-3 py-1 bg-white/5 rounded-full text-[10px] font-black uppercase text-white/50">{selectedCar.año}</span>
                         <span className="px-3 py-1 bg-green-500/10 rounded-full text-[10px] font-black uppercase text-green-400 italic">Disponibilidad Inmediata</span>
                      </div>
                   </div>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                   {[
                     { label: 'Precio USD', val: `$${selectedCar.precio_usd?.toLocaleString()}`, icon: DollarSign },
                     { label: 'Kilometraje', val: `${selectedCar.informacion_general?.kilometraje_number?.toLocaleString()} KM`, icon: Gauge },
                     { label: 'Combustible', val: selectedCar.informacion_general?.combustible || 'N/A', icon: Droplets },
                     { label: 'Transmisión', val: selectedCar.informacion_general?.transmisión || 'N/A', icon: Zap },
                     { label: 'Provincia', val: selectedCar.informacion_general?.provincia || 'N/A', icon: MapPin },
                     { label: 'Año', val: selectedCar.año, icon: Calendar }
                   ].map((spec, i) => (
                      <div key={i} className="p-4 rounded-2xl bg-white/5 border border-white/5 flex flex-col gap-1">
                         <div className="flex items-center gap-1.5 text-white/20 mb-1">
                            {spec.icon && <spec.icon size={12} />}
                            <span className="text-[8px] font-black uppercase tracking-widest">{spec.label}</span>
                         </div>
                         <p className="font-black text-xs uppercase tracking-tight truncate">{spec.val}</p>
                      </div>
                   ))}
                </div>

                <div className="flex flex-col sm:flex-row gap-3 pt-4 border-t border-white/5">
                   <a 
                    href={selectedCar.url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="flex-1 py-4 bg-blue-600 hover:bg-blue-500 rounded-2xl flex items-center justify-center gap-2 font-black transition-all shadow-xl shadow-blue-900/40 text-white"
                   >
                     Ver anuncio original
                     <ExternalLink size={18} />
                   </a>
                   <button 
                    onClick={(e) => {toggleComparison(e, selectedCar); setSelectedCar(null);}}
                    className={cn(
                      "flex-1 py-4 border rounded-2xl flex items-center justify-center gap-2 font-black transition-all",
                      isCarInComparison(selectedCar.car_id) ? "bg-red-500/10 border-red-500/50 text-red-400" : "bg-white/5 border-white/10 text-white hover:bg-white/10"
                    )}
                   >
                     {isCarInComparison(selectedCar.car_id) ? 'Remover de Comparar' : 'Agregar a Comparar'}
                     <Layers size={18} />
                   </button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <style jsx global>{`
        .glass-card {
          background: rgba(255, 255, 255, 0.03);
          backdrop-filter: blur(20px);
          -webkit-backdrop-filter: blur(20px);
        }
        .scrollbar-none::-webkit-scrollbar { display: none; }
      `}</style>
    </main>
  );
}

// Placeholder for missing icons if not found in lucide
function Fuel({ size, className }) {
  return <Droplets size={size} className={className} />;
}
