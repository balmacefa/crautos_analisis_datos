"use client";
import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Search as SearchIcon, 
  ArrowLeft, 
  Filter, 
  Car, 
  TrendingUp, 
  MapPin, 
  Gauge,
  X,
  ChevronDown,
  ExternalLink,
  ShieldCheck,
  Check,
  ArrowRightLeft,
  DollarSign,
  Droplets,
  Zap,
  Layers,
  Calendar,
  Grid,
  List as ListIcon,
  Menu
} from 'lucide-react';
import Link from 'next/link';
import useSWR from 'swr';
import { useTheme } from '@/context/ThemeContext';
import { cn } from '@/lib/utils';
import { getApiBaseUrl, robustFetcher as fetcher } from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Background } from '@/components/layout/Background';
import { BrandModelTree } from '@/components/BrandModelTree';
import { SearchSidebar } from '@/components/SearchSidebar';

export default function SearchExplorer() {
  const { theme } = useTheme();
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');
  const [extraCars, setExtraCars] = useState([]);
  const [page, setPage] = useState(1);
  const [showFilters, setShowFilters] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [selectedCar, setSelectedCar] = useState(null);
  const [comparisonList, setComparisonList] = useState([]);
  const [isComparing, setIsComparing] = useState(false);

  const [filters, setFilters] = useState({
    brands: "",
    models: "",
    year_min: "",
    year_max: "",
    price_min: "",
    price_max: "",
    price_currency: "CRC",
    provinces: "",
    fuels: "",
    transmissions: "",
    fuentes: "",
    sort_by: "año:desc",
  });
  const [viewMode, setViewMode] = useState('list'); // 'list' or 'tree'

  // Debounce search query
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(searchQuery), 400);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  const baseUrl = getApiBaseUrl();

  // SWR for filters data
  const { data: brandsData } = useSWR(`${baseUrl}/api/insights/brands`, fetcher);
  const { data: allModelsData } = useSWR(`${baseUrl}/api/insights/models`, fetcher);
  const { data: provincesData } = useSWR(`${baseUrl}/api/insights/provinces`, fetcher);
  const { data: fuelsData } = useSWR(`${baseUrl}/api/insights/distribution/fuel`, fetcher);
  const { data: transmissionsData } = useSWR(`${baseUrl}/api/insights/distribution/transmission`, fetcher);

  const provinces = useMemo(() => provincesData || [], [provincesData]);
  const fuels = useMemo(() => fuelsData || [], [fuelsData]);
  const transmissions = useMemo(() => transmissionsData || [], [transmissionsData]);
  const allModels = useMemo(() => allModelsData || [], [allModelsData]);

  // Construct URL for V2 API
  const queryUrl = useMemo(() => {
    const params = new URLSearchParams({
      q: debouncedQuery || "*",
      page: "1",
      limit: "20",
      sort_by: filters.sort_by,
      facet_by: "marca,año,combustible,transmisión,provincia,precio_usd,fuente"
    });

    if (filters.brands) params.append("brands", filters.brands);
    if (filters.models) params.append("models", filters.models);
    if (filters.year_min) params.append("year_min", filters.year_min);
    if (filters.year_max) params.append("year_max", filters.year_max);
    if (filters.price_min) params.append("price_min", filters.price_min);
    if (filters.price_max) params.append("price_max", filters.price_max);
    if (filters.price_currency) params.append("price_currency", filters.price_currency);
    if (filters.provinces) params.append("provinces", filters.provinces);
    if (filters.fuels) params.append("fuels", filters.fuels);
    if (filters.transmissions) params.append("transmissions", filters.transmissions);
    if (filters.fuentes) params.append("fuentes", filters.fuentes);

    return `${baseUrl}/api/v2/cars?${params.toString()}`;
  }, [debouncedQuery, filters, baseUrl]);

  const { data: initialData, isLoading: initialLoading } = useSWR(
    queryUrl,
    fetcher,
    { revalidateOnFocus: false, keepPreviousData: true }
  );

  useEffect(() => {
    setExtraCars([]);
    setPage(1);
  }, [queryUrl]);

  const fetchMore = async () => {
    const nextPage = page + 1;
    let url = queryUrl.replace("page=1", `page=${nextPage}`);
    const data = await fetcher(url);
    if (data.cars) {
      setExtraCars((prev) => [...prev, ...data.cars]);
      setPage(nextPage);
    }
  };

  const allCars = useMemo(() => {
    const initial = initialData?.cars || [];
    return [...initial, ...extraCars];
  }, [initialData, extraCars]);

  const facets = useMemo(() => {
    const f = {};
    if (initialData?.facets) {
      initialData.facets.forEach(facet => {
        f[facet.field_name] = facet.counts;
      });
    }
    return f;
  }, [initialData]);

  const total = initialData?.total || 0;

  const toggleComparison = (e, car) => {
    e.stopPropagation();
    setComparisonList(prev => {
      const exists = prev.find(c => c.car_id === car.car_id);
      if (exists) return prev.filter(c => c.car_id !== car.car_id);
      if (prev.length >= 3) return prev;
      return [...prev, car];
    });
  };

  const isCarInComparison = (carId) => comparisonList.some((c) => c.car_id === carId);

  return (
    <main className="min-h-screen w-full relative pb-20">
      <Background />

      {/* Header */}
      <header className="sticky top-0 z-40 glass border-b border-white/10 px-4 md:px-8 py-4 backdrop-blur-xl transition-all">
        <div className="max-w-7xl mx-auto flex flex-col gap-4">
          <div className="flex items-center justify-between w-full">
            <div className="flex items-center gap-4">
              <Link href="/" className="p-2 hover:bg-white/5 rounded-full transition-colors">
                <ArrowLeft size={24} />
              </Link>
              <div>
                <h2 className="text-xl font-black italic tracking-tighter leading-none">Crautos <span className="text-cyan-400">Search</span></h2>
                <p className="text-[10px] text-white/40 uppercase font-black tracking-widest mt-1">Market Explorer v2</p>
              </div>
            </div>

            <button
              className="md:hidden p-2 hover:bg-white/5 rounded-lg transition-colors text-white/60"
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            >
              {isMobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
          </div>

          {/* Search & Actions Container - Hidden on mobile unless menu is open */}
          <div className={cn(
            "flex-col md:flex-row gap-4 w-full md:w-auto items-center md:flex justify-end",
            isMobileMenuOpen ? "flex" : "hidden"
          )}>
            <div className="relative w-full md:max-w-md group">
              <SearchIcon className="absolute left-4 top-1/2 -translate-y-1/2 text-white/30 group-focus-within:text-cyan-400 transition-colors" size={18} />
              <Input
                type="text"
                placeholder="Marca, modelo, año, provincia o precio..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-12 bg-white/5 border-white/10 focus:border-cyan-500/50 focus:ring-cyan-500/20 h-10 md:h-12 text-sm"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery("")}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-white/20 hover:text-white transition-colors"
                >
                  <X size={14} />
                </button>
              )}
            </div>

            <div className="flex items-center gap-3 w-full md:w-auto justify-end">
               <Button
                variant={showFilters ? 'primary' : 'secondary'}
                onClick={() => setShowFilters(!showFilters)}
                className="text-xs uppercase tracking-widest px-5 h-10 md:h-12 w-full md:w-auto"
              >
                <Filter size={16} className="mr-2" />
                Filtros
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Sidebar & Grid Layout */}
      <div className="max-w-7xl mx-auto px-4 py-8 md:px-8 flex flex-col lg:flex-row gap-8">
        {/* Desktop Sidebar Filters */}
        <aside className="hidden lg:block w-72 shrink-0 space-y-8">
          <SearchSidebar
            filters={filters}
            setFilters={setFilters}
            viewMode={viewMode}
            setViewMode={setViewMode}
            facets={facets}
            allModels={allModels}
            provinces={provinces}
            fuels={fuels}
          />
        </aside>

        {/* Main Content Area */}
        <div className="flex-1 space-y-8 z-10">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
            <div>
              <h1 className="text-4xl font-black italic tracking-tighter leading-none">
                {debouncedQuery ? `Resultados para "${debouncedQuery}"` : 'Explora el Mercado'}
              </h1>
              <p className="font-mono text-xs text-white/30 uppercase mt-4 tracking-tighter">
                Mostrando <span className="text-cyan-400 font-bold">{allCars.length}</span> de {total.toLocaleString()} anuncios activos
              </p>
            </div>
          </div>

          {/* Results Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-2 xl:grid-cols-3 gap-6 min-h-[50vh]">
            {allCars.map((car, i) => (
              <Card 
                key={car.car_id + i}
                onClick={() => setSelectedCar(car)}
                className={cn(
                  "p-0 group cursor-pointer",
                  isCarInComparison(car.car_id) && "ring-2 ring-cyan-500 border-transparent shadow-[0_0_30px_rgba(6,182,212,0.3)]"
                )}
              >
                <button 
                  onClick={(e) => toggleComparison(e, car)}
                  className={cn(
                    "absolute top-4 left-4 z-20 w-8 h-8 rounded-xl border flex items-center justify-center transition-all",
                    isCarInComparison(car.car_id) 
                      ? "bg-cyan-600 border-cyan-400 text-white" 
                      : "bg-black/40 border-white/20 text-transparent group-hover:text-white/20"
                  )}
                >
                  <Check size={16} />
                </button>

                <div className="aspect-[16/10] bg-white/5 relative overflow-hidden flex items-center justify-center">
                  {car.imagen_principal ? (
                    <img 
                      src={car.imagen_principal} 
                      alt={`${car.marca} ${car.modelo}`}
                      className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700"
                    />
                  ) : (
                    <Car className="text-white/10 group-hover:scale-110 transition-transform duration-700" size={80} />
                  )}
                  <Badge className="absolute top-4 right-4 z-10" variant="cyan">
                    {car.año}
                  </Badge>
                </div>

                <div className="p-6 space-y-5">
                  <div className="flex justify-between items-start gap-4">
                    <div className="min-w-0">
                      <h3 className="text-xs font-black text-cyan-400 uppercase tracking-widest mb-1">{car.marca}</h3>
                      <p className="text-2xl font-black tracking-tighter leading-none truncate">{car.modelo}</p>
                    </div>
                    <div className="flex flex-col items-end shrink-0 text-right">
                      <span className="text-[10px] font-black text-white/60 uppercase tracking-tighter">{car.año}</span>
                      <span className="text-[8px] font-black text-white/30 uppercase tracking-widest truncate max-w-[70px]">{car.informacion_general?.transmisión}</span>
                      <span className="text-[8px] font-black text-white/30 uppercase tracking-widest truncate max-w-[70px]">{car.informacion_general?.combustible}</span>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4 py-4 border-y border-white/5">
                    <div className="flex items-center gap-2 text-white/50">
                      <Gauge size={14} className="text-cyan-500" />
                      <span className="text-[11px] font-black uppercase truncate">{car.informacion_general?.kilometraje_number?.toLocaleString() || '0'} KM</span>
                    </div>
                    <div className="flex items-center gap-2 text-white/50">
                      <MapPin size={14} className="text-cyan-500" />
                      <span className="text-[11px] font-black uppercase truncate">{car.informacion_general?.provincia || 'N/A'}</span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-[10px] font-black text-white/20 uppercase tracking-widest">Precio</p>
                      <div className="flex flex-col">
                        <span className="text-2xl font-black font-mono text-emerald-400 tracking-tighter leading-none">
                          ₡{car.precio_crc?.toLocaleString()}
                        </span>
                        <span className="text-xs font-bold font-mono text-white/40 tracking-tighter mt-1">
                          ${car.precio_usd?.toLocaleString()}
                        </span>
                      </div>
                    </div>
                    <button 
                      onClick={(e) => {
                        e.stopPropagation();
                        window.open(car.url, '_blank');
                      }}
                      className="w-12 h-12 bg-white/5 hover:bg-cyan-600 rounded-2xl flex items-center justify-center transition-all hover:scale-110 active:scale-95 shrink-0 group/btn"
                      title="Ver anuncio original"
                    >
                      <ExternalLink className="text-white/20 group-hover/btn:text-white" size={18} />
                    </button>
                  </div>
                </div>
              </Card>
            ))}

            {initialLoading && allCars.length === 0 && Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="glass rounded-[2.5rem] h-[400px] animate-pulse opacity-10" />
            ))}
          </div>

          {!initialLoading && allCars.length === 0 && (
            <div className="text-center py-20 glass rounded-[2.5rem] border border-white/5">
              <SearchIcon size={64} className="mx-auto text-white/10 mb-4" />
              <h2 className="text-2xl font-bold">No encontramos lo que buscas</h2>
              <p className="text-white/40 mt-2">Prueba ajustando los filtros o cambiando la búsqueda.</p>
              <Button 
                variant="primary" 
                className="mt-6"
                onClick={() => {
                  setSearchQuery("");
                  setFilters({
                    brands: "", year_min: "", year_max: "", price_min: "", price_max: "",
                    provinces: "", fuels: "", transmissions: "", sort_by: "año:desc"
                  });
                }}
              >
                Limpiar filtros
              </Button>
            </div>
          )}

          {allCars.length < total && !initialLoading && (
            <div className="mt-12 flex justify-center">
              <Button variant="secondary" onClick={fetchMore} size="lg" className="text-white/40 hover:text-white uppercase tracking-[0.2em]">
                Cargar más unidades
              </Button>
            </div>
          )}
        </div>
      </div>

      {/* Comparison Tray */}
      <AnimatePresence>
        {comparisonList.length > 0 && (
          <motion.div
            initial={{ y: 100 }} animate={{ y: 0 }} exit={{ y: 100 }}
            className="fixed bottom-0 left-0 right-0 z-50 glass border-t border-white/10 px-6 py-4 backdrop-blur-2xl"
          >
            <div className="max-w-7xl mx-auto flex items-center justify-between gap-6">
              <div className="flex items-center gap-4 overflow-x-auto pb-2 scrollbar-none">
                <div className="flex -space-x-3">
                  {comparisonList.map((car) => (
                    <div key={car.car_id} className="w-12 h-12 rounded-2xl bg-cyan-600 border-2 border-zinc-900 flex items-center justify-center shadow-xl overflow-hidden relative">
                      {car.imagen_principal ? (
                        <img src={car.imagen_principal} alt={car.marca} className="w-full h-full object-cover" />
                      ) : (
                        <Car size={16} className="text-white" />
                      )}
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
                <Button variant="ghost" onClick={() => setComparisonList([])} className="p-4 rounded-2xl"><X size={20} /></Button>
                <Button 
                  variant="primary"
                  disabled={comparisonList.length < 2}
                  onClick={() => setIsComparing(true)}
                  className="gap-3 px-8 py-4 uppercase tracking-widest"
                >
                  <ArrowRightLeft size={18} /> Comparar ahora
                </Button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>


      {/* Mobile Filter Modal */}
      <AnimatePresence>
        {showFilters && (
          <motion.div
            initial={{ opacity: 0, y: '100%' }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className="fixed inset-0 z-[70] bg-black/95 backdrop-blur-2xl flex flex-col p-4 md:hidden overflow-y-auto"
          >
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-black italic tracking-tighter text-cyan-400">Filtros</h2>
              <Button variant="ghost" onClick={() => setShowFilters(false)} className="p-2 rounded-full">
                <X size={24} />
              </Button>
            </div>

            <SearchSidebar
              filters={filters}
              setFilters={setFilters}
              viewMode={viewMode}
              setViewMode={setViewMode}
              facets={facets}
              allModels={allModels}
              provinces={provinces}
              fuels={fuels}
            />

            <div className="mt-8 mb-4">
              <Button
                variant="primary"
                className="w-full py-4 text-lg font-bold"
                onClick={() => setShowFilters(false)}
              >
                Ver Resultados
              </Button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Comparison Modal */}
      <AnimatePresence>
        {isComparing && (
          <motion.div
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="fixed inset-0 z-[60] bg-black/95 backdrop-blur-2xl flex flex-col p-4 md:p-12 overflow-y-auto"
          >
            <div className="max-w-6xl mx-auto w-full space-y-12">
              <div className="flex justify-between items-center">
                <div>
                  <h2 className="text-4xl font-black italic tracking-tighter text-cyan-400">Batalla de Titanes</h2>
                  <p className="text-white/40 uppercase font-black text-xs tracking-widest mt-2">Comparativa técnica lado a lado</p>
                </div>
                <Button variant="ghost" onClick={() => setIsComparing(false)} className="p-4 rounded-full"><X size={24} /></Button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {comparisonList.map((car) => (
                  <Card key={car.car_id} className="p-8 space-y-8 flex flex-col bg-white/5 border-white/10" hover={false}>
                    <div className="w-full aspect-[16/10] bg-black/20 rounded-2xl overflow-hidden relative flex items-center justify-center shrink-0">
                      {car.imagen_principal ? (
                        <img src={car.imagen_principal} alt={car.marca} className="w-full h-full object-cover" />
                      ) : (
                        <Car size={60} className="text-white/20" />
                      )}
                    </div>
                    <div className="text-center space-y-2">
                      <p className="text-xs font-black text-cyan-400 uppercase tracking-widest">{car.marca}</p>
                      <h3 className="text-2xl font-black tracking-tighter leading-none italic">{car.modelo}</h3>
                      <p className="text-3xl font-mono font-black text-green-400 mt-4">${car.precio_usd?.toLocaleString()}</p>
                    </div>

                    <div className="space-y-6 pt-6 border-t border-white/10">
                      {[
                        { label: 'Año', val: car.año },
                        { label: 'Recorrido', val: `${car.informacion_general?.kilometraje_number?.toLocaleString()} KM` },
                        { label: 'Combustible', val: car.informacion_general?.combustible || 'N/A' },
                        { label: 'Transmisión', val: car.informacion_general?.transmisión || 'N/A' },
                        { label: 'Provincia', val: car.informacion_general?.provincia || 'N/A' }
                      ].map((s, i) => (
                        <div key={i} className="space-y-1">
                          <p className="text-[10px] text-white/30 uppercase font-black tracking-widest">{s.label}</p>
                          <p className="font-bold text-lg">{s.val}</p>
                        </div>
                      ))}
                    </div>

                    <Button variant="outline" className="w-full" onClick={() => window.open(car.url, '_blank')}>
                      Ver en Crautos <ExternalLink size={14} className="ml-2" />
                    </Button>
                  </Card>
                ))}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Selected Car Details Modal */}
      <AnimatePresence>
        {selectedCar && !isComparing && (
          <motion.div
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md"
            onClick={() => setSelectedCar(null)}
          >
            <motion.div
              initial={{ scale: 0.9, y: 20 }} animate={{ scale: 1, y: 0 }} exit={{ scale: 0.9, y: 20 }}
              onClick={(e) => e.stopPropagation()}
              className="w-full max-w-2xl bg-zinc-900 rounded-[2.5rem] border border-white/10 p-8 overflow-hidden relative"
            >
              <Button variant="ghost" onClick={() => setSelectedCar(null)} className="absolute top-6 right-6 p-2 h-10 w-10 rounded-full"><X size={20} /></Button>

              <div className="flex flex-col gap-8">
                <div className="flex gap-6 items-start">
                  <div className="w-24 h-24 bg-cyan-600/20 rounded-3xl flex items-center justify-center shrink-0 border border-cyan-500/30 overflow-hidden">
                    {selectedCar.imagen_principal ? (
                      <img src={selectedCar.imagen_principal} alt={selectedCar.marca} className="w-full h-full object-cover" />
                    ) : (
                      <Car size={40} className="text-cyan-400" />
                    )}
                  </div>
                  <div className="flex-1">
                    <p className="text-cyan-400 font-extrabold uppercase tracking-widest text-[10px] mb-1">{selectedCar.marca}</p>
                    <h2 className="text-4xl font-black italic tracking-tighter leading-[0.9]">{selectedCar.modelo}</h2>
                    <div className="flex gap-3 mt-4">
                      <Badge variant="secondary">{selectedCar.año}</Badge>
                      <Badge variant="emerald italic">Disponibilidad Inmediata</Badge>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  {[
                    { label: "Precio USD", val: `$${selectedCar.precio_usd?.toLocaleString()}`, icon: DollarSign },
                    { label: "Kilometraje", val: `${selectedCar.informacion_general?.kilometraje_number?.toLocaleString()} KM`, icon: Gauge },
                    { label: "Combustible", val: selectedCar.informacion_general?.combustible || "N/A", icon: Droplets },
                    { label: "Transmisión", val: selectedCar.informacion_general?.transmisión || "N/A", icon: Zap },
                    { label: "Provincia", val: selectedCar.informacion_general?.provincia || "N/A", icon: MapPin },
                    { label: "Año", val: selectedCar.año, icon: Calendar },
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
                  <Button variant="primary" className="flex-1" onClick={() => window.open(selectedCar.url, '_blank')}>
                    Ver anuncio original <ExternalLink size={18} className="ml-2" />
                  </Button>
                  <Button 
                    variant={isCarInComparison(selectedCar.car_id) ? 'outline' : 'secondary'} 
                    className="flex-1"
                    onClick={(e) => { toggleComparison(e, selectedCar); setSelectedCar(null); }}
                  >
                    {isCarInComparison(selectedCar.car_id) ? "Remover de Comparar" : "Agregar a Comparar"}
                    <Layers size={18} className="ml-2" />
                  </Button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <style jsx global>{`
        .glass {
          background: rgba(255, 255, 255, 0.03);
          backdrop-filter: blur(20px);
          -webkit-backdrop-filter: blur(20px);
        }
        .scrollbar-none::-webkit-scrollbar {
          display: none;
        }
      `}</style>
    </main>
  );
}
