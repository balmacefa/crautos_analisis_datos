"use client"
import React, { useState, useEffect, useMemo } from 'react';
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
  DollarSign
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

export default function SearchExplorer() {
  const { theme } = useTheme();
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
      if (prev.length >= 3) return prev;
      return [...prev, car];
    });
  };

  const isCarInComparison = (carId) => comparisonList.some(c => c.car_id === carId);

  return (
    <main className="min-h-screen w-full relative pb-20">
      <Background />

      {/* Header */}
      <header className="sticky top-0 z-40 glass border-b border-white/10 px-4 md:px-8 py-4 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row gap-4 items-center justify-between">
          <div className="flex items-center gap-4 w-full md:w-auto">
            <Link href="/" className="p-2 hover:bg-white/5 rounded-full transition-colors">
              <ArrowLeft size={24} />
            </Link>
            <div>
              <h2 className="text-xl font-black italic tracking-tighter leading-none">Crautos <span className="text-cyan-400">Search</span></h2>
              <p className="text-[10px] text-white/40 uppercase font-black tracking-widest mt-1">Market Explorer v2</p>
            </div>
          </div>

          <div className="relative w-full md:max-w-md group">
            <SearchIcon className="absolute left-4 top-1/2 -translate-y-1/2 text-white/30 group-focus-within:text-cyan-400 transition-colors" size={18} />
            <Input 
              type="text" 
              placeholder="Busca por marca, modelo o año..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-12"
            />
          </div>

          <div className="flex items-center gap-3 w-full md:w-auto justify-end">
             <Button 
              variant={showFilters ? 'primary' : 'secondary'}
              onClick={() => setShowFilters(!showFilters)}
              className="text-xs uppercase tracking-widest px-5 py-3"
            >
              <Filter size={16} className="mr-2" />
              Filtros
            </Button>
          </div>
        </div>
      </header>

      {/* Sidebar & Grid Layout */}
      <div className="max-w-7xl mx-auto px-4 py-8 md:px-8 flex flex-col lg:flex-row gap-8">
        
        {/* Desktop Sidebar Filters */}
        <aside className="hidden lg:block w-72 shrink-0 space-y-8">
          <Card className="p-6 space-y-6" hover={false}>
            <h3 className="text-sm font-black uppercase tracking-widest flex items-center gap-2">
              <TrendingUp size={16} className="text-cyan-400" />
              Parámetros
            </h3>
            
            <div className="space-y-6">
              <div className="space-y-3">
                <label className="text-[10px] font-black text-white/40 uppercase tracking-widest">Rango de Precio (USD)</label>
                <div className="flex gap-2">
                   <Input type="number" placeholder="Min" value={filters.price_min} onChange={e => setFilters(p => ({...p, price_min: e.target.value}))} className="h-10" />
                   <Input type="number" placeholder="Max" value={filters.price_max} onChange={e => setFilters(p => ({...p, price_max: e.target.value}))} className="h-10" />
                </div>
              </div>

              <div className="space-y-3">
                <label className="text-[10px] font-black text-white/40 uppercase tracking-widest">Provincia</label>
                <Select 
                  value={filters.provincias} 
                  onChange={e => setFilters(p => ({...p, provinces: e.target.value}))}
                  className="h-10"
                >
                  <option value="">Todas las provincias</option>
                  {provinces.map(p => (
                    <option key={p.provincia} value={p.provincia}>{p.provincia}</option>
                  ))}
                </Select>
              </div>

              <div className="space-y-3">
                <label className="text-[10px] font-black text-white/40 uppercase tracking-widest">Ordenar por</label>
                <Select 
                  value={filters.sort_by} 
                  onChange={e => setFilters(p => ({...p, sort_by: e.target.value}))}
                  className="h-10"
                >
                  <option value="año:desc">Más Recientes</option>
                  <option value="precio_usd:asc">Menor Precio</option>
                  <option value="precio_usd:desc">Mayor Precio</option>
                  <option value="kilometraje_number:asc">Menor Kilometraje</option>
                </Select>
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
        </aside>

        {/* Main Content Area */}
        <div className="flex-1 space-y-8 z-10">
          <div>
            <h1 className="text-4xl font-black italic tracking-tighter leading-none">
              {debouncedQuery ? `Resultados para "${debouncedQuery}"` : 'Explora el Mercado'}
            </h1>
            <p className="font-mono text-xs text-white/30 uppercase mt-4 tracking-tighter">
              Mostrando <span className="text-cyan-400 font-bold">{allCars.length}</span> de {total.toLocaleString()} anuncios
            </p>
          </div>

          {/* Results Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-2 xl:grid-cols-3 gap-6 min-h-[50vh]">
            {allCars.map((car, i) => (
              <Card 
                key={car.car_id + i}
                onClick={() => setSelectedCar(car)}
                className={cn(
                  "p-0 group",
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
                  <Car className="text-white/10 group-hover:scale-110 transition-transform duration-700" size={80} />
                  <Badge className="absolute top-4 right-4" variant="cyan">
                    {car.año}
                  </Badge>
                </div>

                <div className="p-6 space-y-5">
                  <div>
                    <h3 className="text-xs font-black text-cyan-400 uppercase tracking-widest mb-1">{car.marca}</h3>
                    <p className="text-2xl font-black tracking-tighter leading-none truncate">{car.modelo}</p>
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
                      <p className="text-[10px] font-black text-white/20 uppercase tracking-widest">Precio Hoy</p>
                      <p className="text-3xl font-black font-mono text-green-400 tracking-tighter">
                        ${car.precio_usd?.toLocaleString()}
                      </p>
                    </div>
                    <Button variant="secondary" className="p-3">
                      <ArrowRightLeft size={18} />
                    </Button>
                  </div>
                </div>
              </Card>
            ))}
          </div>

          {/* Load More */}
          {allCars.length < total && !initialLoading && (
            <div className="mt-12 flex justify-center">
              <Button variant="secondary" onClick={fetchMore} size="lg">
                Cargar más unidades
              </Button>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
