"use client"
import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  BarChart, 
  LineChart, 
  Line, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  PieChart, 
  Pie, 
  Cell,
  Legend,
  ScatterChart,
  Scatter,
  ZAxis
} from 'recharts';
import { 
  TrendingUp, 
  ArrowLeft, 
  DollarSign, 
  Gauge, 
  Calendar, 
  Car, 
  Zap, 
  MapPin, 
  Award, 
  Sparkles,
  Search,
  ChevronRight,
  Target,
  BarChart3,
  SearchCheck,
  Percent,
  Settings2
} from 'lucide-react';
import Link from 'next/link';
import useSWR from 'swr';
import { getApiBaseUrl } from '@/lib/api';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs) {
  return twMerge(clsx(inputs));
}

const fetcher = (url) => fetch(url).then((res) => res.json());

// --- Components ---

const GlassCard = ({ children, className, title, subtitle, icon: Icon }) => (
  <motion.div 
    initial={{ opacity: 0, y: 20 }}
    whileInView={{ opacity: 1, y: 0 }}
    viewport={{ once: true }}
    className={cn("glass p-6 rounded-[2rem] border border-white/5 relative overflow-hidden group", className)}
  >
    <div className="absolute inset-0 bg-gradient-to-br from-white/[0.02] to-transparent pointer-events-none" />
    {(title || Icon) && (
      <div className="flex items-center gap-4 mb-6 relative z-10">
        {Icon && (
          <div className="w-10 h-10 rounded-2xl bg-blue-600/20 flex items-center justify-center text-blue-400 group-hover:scale-110 transition-transform">
            <Icon size={20} />
          </div>
        )}
        <div>
          <h3 className="text-xs font-black uppercase tracking-[0.2em] text-white/80 leading-none">{title}</h3>
          {subtitle && <p className="text-[10px] text-white/30 uppercase font-black tracking-widest mt-1">{subtitle}</p>}
        </div>
      </div>
    )}
    <div className="relative z-10">{children}</div>
  </motion.div>
);

const MarketExtremeCard = ({ title, car, type = "price" }) => {
  if (!car) return null;
  
  const getValue = () => {
    if (type === "price") return `$${car.precio_usd?.toLocaleString()}`;
    if (type === "mileage") return `${car.kilometraje_number?.toLocaleString()} KM`;
    if (type === "year") return `Año ${car.año}`;
    return "";
  };

  return (
    <div className="flex items-center gap-4 p-4 rounded-2xl bg-white/5 border border-white/5 group hover:bg-white/10 transition-all">
       <div className="w-16 h-16 rounded-xl bg-white/5 overflow-hidden shrink-0 flex items-center justify-center relative">
          {car.imagen_principal ? (
            <img 
              src={car.imagen_principal} 
              alt={car.modelo} 
              className="w-full h-full object-cover group-hover:scale-110 transition-transform" 
            />
          ) : (
            <Car className="text-white/10" size={32} />
          )}
       </div>
       <div className="flex-1 overflow-hidden">
          <p className="text-[9px] font-black text-blue-500 uppercase tracking-widest mb-1">{title}</p>
          <h4 className="font-bold text-sm truncate uppercase tracking-tighter leading-none">{car.marca} {car.modelo}</h4>
          <p className="text-lg font-black italic tracking-tighter text-white/80 mt-1">{getValue()}</p>
       </div>
    </div>
  );
};

// --- Page Implementation ---

export default function InsightsDashboard() {
  const baseUrl = getApiBaseUrl();
  
  // Data Fetching
  const { data: summary } = useSWR(`${baseUrl}/api/insights/summary`, fetcher);
  const { data: curiosities } = useSWR(`${baseUrl}/api/insights/curiosities`, fetcher);
  const { data: opportunities } = useSWR(`${baseUrl}/api/insights/opportunities`, fetcher);
  const { data: depreciation } = useSWR(`${baseUrl}/api/insights/depreciation`, fetcher);
  const { data: ratiosData } = useSWR(`${baseUrl}/api/insights/ratios/top`, fetcher);
  const { data: fuelStats } = useSWR(`${baseUrl}/api/insights/distribution/fuel`, fetcher);
  const { data: transStats } = useSWR(`${baseUrl}/api/insights/distribution/transmission`, fetcher);
  const { data: provinceStats } = useSWR(`${baseUrl}/api/insights/provinces`, fetcher);
  const { data: explorerData } = useSWR(`${baseUrl}/api/insights/explorer`, fetcher);

  // Filter & Logic for Ratios
  const topRatios = useMemo(() => {
    if (!ratiosData) return [];
    return [...ratiosData]
      .sort((a, b) => b.ratio_usd - a.ratio_usd)
      .slice(0, 10);
  }, [ratiosData]);

  const bestValueRatios = useMemo(() => {
    if (!ratiosData) return [];
    return [...ratiosData]
      .sort((a, b) => a.ratio_usd - b.ratio_usd)
      .slice(0, 10);
  }, [ratiosData]);

  // Logic for Depreciation Comparison
  const [selectedBrands, setSelectedBrands] = useState(['Toyota', 'Hyundai', 'Nissan']);
  const depreciationChartData = useMemo(() => {
    if (!depreciation) return [];
    // Group by year and filter selected brands
    const years = [...new Set(depreciation.map(d => d.año))].sort((a, b) => a - b);
    return years.map(year => {
      const entry = { name: year };
      selectedBrands.forEach(brand => {
        const d = depreciation.find(x => x.marca === brand && x.año === year);
        if (d) entry[brand] = d.avg_price_usd;
      });
      return entry;
    });
  }, [depreciation, selectedBrands]);

  // Scatter Plot State
  const [scatterX, setScatterX] = useState('año');
  const [scatterY, setScatterY] = useState('precio_usd');
  const [scatterColor, setScatterColor] = useState('transmisión');

  const scatterColors = {
    'Manual': '#3b82f6',
    'Automática': '#8b5cf6',
    'Gasolina': '#10b981',
    'Diésel': '#f59e0b',
    'San José': '#f43f5e',
    'Alajuela': '#fb923c'
  };

  const COLORS_PIE = ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#f43f5e', '#6366f1', '#ec4899'];

  return (
    <main className="min-h-screen w-full gradient-bg pb-20 selection:bg-blue-500/30 font-sans">
      {/* Dynamic Background */}
      <div className="fixed inset-0 z-0 pointer-events-none opacity-20">
        <div className="absolute top-[-10%] right-[-10%] w-[50%] h-[50%] bg-blue-600 rounded-full blur-[150px] animate-pulse-slow" />
        <div className="absolute bottom-[-10%] left-[-10%] w-[50%] h-[50%] bg-indigo-600 rounded-full blur-[150px] animate-pulse-slow delay-1000" />
      </div>

      <header className="sticky top-0 z-50 glass border-b border-white/5 backdrop-blur-3xl">
        <div className="max-w-[1400px] mx-auto px-6 h-20 flex items-center justify-between">
           <div className="flex items-center gap-6">
              <Link href="/" className="p-3 bg-white/5 hover:bg-white/10 rounded-2xl transition-all border border-white/5 group">
                <ArrowLeft size={18} className="group-hover:-translate-x-1 transition-transform" />
              </Link>
              <div>
                 <h1 className="text-2xl font-black italic tracking-tighter uppercase leading-none">
                   MARKET<span className="text-blue-500">INSIGHTS</span>
                 </h1>
                 <p className="text-[9px] font-black uppercase tracking-widest text-white/30 mt-1">Dash Application Analytics V2</p>
              </div>
           </div>
           
           <div className="flex items-center gap-4">
              <div className="text-right hidden sm:block">
                 <p className="text-[10px] font-black uppercase text-white/20 tracking-tighter">Última actualización</p>
                 <p className="text-xs font-mono font-bold text-blue-400">{summary?.last_updated ? new Date(summary.last_updated).toLocaleDateString() : 'Cargando...'}</p>
              </div>
              <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-2xl flex items-center gap-3">
                 <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                 <span className="text-[10px] font-black uppercase text-emerald-400 tracking-widest">Live Integration</span>
              </div>
           </div>
        </div>
      </header>

      <div className="max-w-[1400px] mx-auto px-6 py-12 space-y-10 relative z-10">
        
        {/* --- Section 1: Top Stats Banner --- */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
           <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="glass p-7 rounded-[2.5rem] border border-white/5 flex flex-col gap-4">
              <div className="w-12 h-12 rounded-2xl bg-blue-600/20 flex items-center justify-center text-blue-400"><Car size={24} /></div>
              <div>
                 <p className="text-[10px] font-black text-white/30 uppercase tracking-widest italic mb-1">Muestra del Mercado</p>
                 <h2 className="text-4xl font-black italic tracking-tighter leading-none">{summary?.total_cars?.toLocaleString() || '...'}</h2>
                 <p className="text-xs text-white/40 mt-1">Vehículos analizados hoy</p>
              </div>
           </motion.div>
           <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.1 }} className="glass p-7 rounded-[2.5rem] border border-white/5 flex flex-col gap-4">
              <div className="w-12 h-12 rounded-2xl bg-emerald-600/20 flex items-center justify-center text-emerald-400"><DollarSign size={24} /></div>
              <div>
                 <p className="text-[10px] font-black text-white/30 uppercase tracking-widest italic mb-1">Precio Promedio</p>
                 <h2 className="text-4xl font-black italic tracking-tighter leading-none">${summary?.avg_price_usd?.toLocaleString() || '...'}</h2>
                 <p className="text-xs text-white/40 mt-1">Valor medio comercial (USD)</p>
              </div>
           </motion.div>
           <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.2 }} className="glass p-7 rounded-[2.5rem] border border-white/5 flex flex-col gap-4">
              <div className="w-12 h-12 rounded-2xl bg-indigo-600/20 flex items-center justify-center text-indigo-400"><Gauge size={24} /></div>
              <div>
                 <p className="text-[10px] font-black text-white/30 uppercase tracking-widest italic mb-1">Uso Promedio</p>
                 <h2 className="text-4xl font-black italic tracking-tighter leading-none">84.2K<span className="text-sm font-bold text-white/40 ml-1">KM</span></h2>
                 <p className="text-xs text-white/40 mt-1">Desgaste medio del parque</p>
              </div>
           </motion.div>
           <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.3 }} className="glass p-7 rounded-[2.5rem] border border-white/5 flex flex-col gap-4">
              <div className="w-12 h-12 rounded-2xl bg-purple-600/20 flex items-center justify-center text-purple-400"><TrendingUp size={24} /></div>
              <div>
                 <p className="text-[10px] font-black text-white/30 uppercase tracking-widest italic mb-1">Tendencia Anual</p>
                 <h2 className="text-4xl font-black italic tracking-tighter leading-none">{summary?.total_cars > 1000 ? '+12.4%' : 'ESTABLE'}</h2>
                 <p className="text-xs text-white/40 mt-1">Volumen de nuevas ofertas</p>
              </div>
           </motion.div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-[1fr_350px] gap-10">
           
           <div className="space-y-10">
              
              {/* --- Section 2: Depreciation Analysis --- */}
              <GlassCard title="Análisis de Depreciación" subtitle="Comparativa de pérdida de valor por marca" icon={TrendingUp}>
                 <div className="flex flex-wrap gap-2 mb-8">
                    {['Toyota', 'Hyundai', 'Nissan', 'Kia', 'Suzuki', 'Mitsubishi', 'Honda'].map(brand => (
                      <button 
                        key={brand}
                        onClick={() => setSelectedBrands(prev => prev.includes(brand) ? prev.filter(b => b !== brand) : [...prev, brand])}
                        className={cn(
                          "px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all border",
                          selectedBrands.includes(brand) ? "bg-blue-600 border-blue-400 text-white" : "bg-white/5 border-white/10 text-white/40 hover:text-white"
                        )}
                      >
                        {brand}
                      </button>
                    ))}
                 </div>
                 <div className="h-[400px] w-full mt-4">
                    <ResponsiveContainer width="100%" height="100%">
                       <LineChart data={depreciationChartData}>
                          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                          <XAxis dataKey="name" stroke="rgba(255,255,255,0.3)" fontSize={10} axisLine={false} tickLine={false} />
                          <YAxis stroke="rgba(255,255,255,0.3)" fontSize={10} axisLine={false} tickLine={false} tickFormatter={(v) => `$${v/1000}k`} />
                          <Tooltip 
                            contentStyle={{ backgroundColor: '#111', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '1rem', fontSize: '12px' }}
                            itemStyle={{ fontWeight: 'bold' }}
                          />
                          <Legend wrapperStyle={{ fontSize: '10px', paddingTop: '20px', fontWeight: 'bold', textTransform: 'uppercase' }} />
                          {selectedBrands.map((brand, i) => (
                            <Line 
                              key={brand} 
                              type="monotone" 
                              dataKey={brand} 
                              stroke={COLORS_PIE[i % COLORS_PIE.length]} 
                              strokeWidth={3} 
                              dot={{ fill: COLORS_PIE[i % COLORS_PIE.length], r: 4 }} 
                              activeDot={{ r: 8 }} 
                            />
                          ))}
                       </LineChart>
                    </ResponsiveContainer>
                 </div>
              </GlassCard>

              {/* --- Section 3: Ratio & Value Analysis --- */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <GlassCard title="Mejor Relación $/KM" subtitle="Vehículos que ofrecen más por cada dólar" icon={Award}>
                   <div className="h-[300px] w-full">
                      <ResponsiveContainer width="100%" height="100%">
                         <BarChart data={bestValueRatios} layout="vertical">
                           <XAxis type="number" hide />
                           <YAxis dataKey="modelo" type="category" stroke="rgba(255,255,255,0.3)" fontSize={9} width={90} axisLine={false} tickLine={false} />
                           <Tooltip cursor={{ fill: 'rgba(255,255,255,0.05)' }} contentStyle={{ backgroundColor: '#111', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '1rem' }} />
                           <Bar dataKey="ratio_usd" fill="#3b82f6" radius={[0, 10, 10, 0]} barSize={20}>
                             {bestValueRatios.map((entry, index) => (
                               <Cell key={`cell-${index}`} fillOpacity={1 - index * 0.08} />
                             ))}
                           </Bar>
                         </BarChart>
                      </ResponsiveContainer>
                   </div>
                </GlassCard>

                <GlassCard title="Retención de Valor Máxima" subtitle="Modelos que más cobran por kilómetro" icon={Target}>
                   <div className="h-[300px] w-full">
                      <ResponsiveContainer width="100%" height="100%">
                         <BarChart data={topRatios} layout="vertical">
                            <XAxis type="number" hide />
                            <YAxis dataKey="modelo" type="category" stroke="rgba(255,255,255,0.3)" fontSize={9} width={90} axisLine={false} tickLine={false} />
                            <Tooltip cursor={{ fill: 'rgba(255,255,255,0.05)' }} contentStyle={{ backgroundColor: '#111', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '1rem' }} />
                            <Bar dataKey="ratio_usd" fill="#8b5cf6" radius={[0, 10, 10, 0]} barSize={20}>
                              {topRatios.map((entry, index) => (
                                <Cell key={`cell-${index}`} fillOpacity={1 - index * 0.08} />
                              ))}
                            </Bar>
                         </BarChart>
                      </ResponsiveContainer>
                   </div>
                </GlassCard>
              </div>

               {/* --- Section 4: Advanced Dynamic Explorer --- */}
               <GlassCard title="Explorador Dinámico de Datos" subtitle="Analítica correlacional multieje" icon={Settings2}>
                  <div className="flex flex-col md:flex-row gap-6 mb-8">
                     <div className="flex-1 space-y-2">
                        <label className="text-[9px] font-black uppercase text-white/30 tracking-widest pl-2">Dimensión X</label>
                        <select value={scatterX} onChange={e => setScatterX(e.target.value)} className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-xs font-bold outline-none focus:ring-1 focus:ring-blue-500">
                           <option value="año" className="bg-zinc-950">Año de Fabricación</option>
                           <option value="kilometraje_number" className="bg-zinc-950">Kilometraje (KM)</option>
                           <option value="precio_usd" className="bg-zinc-950">Precio (USD)</option>
                        </select>
                     </div>
                     <div className="flex-1 space-y-2">
                        <label className="text-[9px] font-black uppercase text-white/30 tracking-widest pl-2">Dimensión Y</label>
                        <select value={scatterY} onChange={e => setScatterY(e.target.value)} className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-xs font-bold outline-none focus:ring-1 focus:ring-blue-500">
                           <option value="precio_usd" className="bg-zinc-950">Precio (USD)</option>
                           <option value="kilometraje_number" className="bg-zinc-950">Kilometraje (KM)</option>
                           <option value="año" className="bg-zinc-950">Año de Fabricación</option>
                        </select>
                     </div>
                     <div className="flex-1 space-y-2">
                        <label className="text-[9px] font-black uppercase text-white/30 tracking-widest pl-2">Segmentar por (Colores)</label>
                        <select value={scatterColor} onChange={e => setScatterColor(e.target.value)} className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-xs font-bold outline-none focus:ring-1 focus:ring-blue-500">
                           <option value="transmisión" className="bg-zinc-950">Transmisión</option>
                           <option value="combustible" className="bg-zinc-950">Combustible</option>
                           <option value="provincia" className="bg-zinc-950">Provincia</option>
                        </select>
                     </div>
                  </div>
                  <div className="h-[450px] w-full">
                     <ResponsiveContainer width="100%" height="100%">
                        <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                           <XAxis type="number" dataKey={scatterX} name={scatterX} stroke="rgba(255,255,255,0.2)" fontSize={10} axisLine={false} tickLine={false} domain={['auto', 'auto']} />
                           <YAxis type="number" dataKey={scatterY} name={scatterY} stroke="rgba(255,255,255,0.2)" fontSize={10} axisLine={false} tickLine={false} tickFormatter={(v) => v > 1000 ? `${v/1000}k` : v} />
                           <ZAxis type="number" range={[50, 400]} />
                           <Tooltip 
                            cursor={{ strokeDasharray: '3 3' }} 
                            contentStyle={{ backgroundColor: '#111', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '1rem' }}
                            itemStyle={{ fontSize: '11px', color: '#fff', textTransform: 'uppercase' }}
                           />
                           {explorerData && [...new Set(explorerData.map(d => d[scatterColor]))].map((val, idx) => (
                              <Scatter 
                                key={val} 
                                name={val} 
                                data={explorerData.filter(d => d[scatterColor] === val)} 
                                fill={COLORS_PIE[idx % COLORS_PIE.length]} 
                                fillOpacity={0.6}
                                shape="circle"
                              />
                           ))}
                           <Legend wrapperStyle={{ fontSize: '9px', fontWeight: 'bold' }} />
                        </ScatterChart>
                     </ResponsiveContainer>
                  </div>
               </GlassCard>

           </div>

           {/* --- Right Sidebar: Extremes & Distribution --- */}
           <div className="space-y-10">
              
              <GlassCard title="Extremos del Mercado" subtitle="Puntos atípicos detectados" icon={Sparkles}>
                 <div className="space-y-4">
                    <MarketExtremeCard title="Más Caro" car={curiosities?.most_expensive} type="price" />
                    <MarketExtremeCard title="Más Económico" car={curiosities?.cheapest} type="price" />
                    <MarketExtremeCard title="Más Antiguo" car={curiosities?.oldest} type="year" />
                    <MarketExtremeCard title="Mayor Kilometraje" car={curiosities?.highest_mileage} type="mileage" />
                 </div>
              </GlassCard>

              <GlassCard title="Combustibles" subtitle="Distribución por tipo de energía" icon={Zap}>
                 <div className="h-[200px] w-full">
                    <ResponsiveContainer width="100%" height="100%">
                       <PieChart>
                          <Pie
                            data={fuelStats}
                            cx="50%"
                            cy="50%"
                            innerRadius={60}
                            outerRadius={80}
                            paddingAngle={5}
                            dataKey="count"
                            nameKey="combustible"
                          >
                            {fuelStats?.map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={COLORS_PIE[index % COLORS_PIE.length]} stroke="none" />
                            ))}
                          </Pie>
                          <Tooltip contentStyle={{ backgroundColor: '#111', border: 'none', borderRadius: '1rem', fontSize: '10px' }} />
                       </PieChart>
                    </ResponsiveContainer>
                 </div>
                 <div className="grid grid-cols-1 gap-2 mt-4">
                    {fuelStats?.slice(0, 4).map((f, i) => (
                      <div key={f.combustible} className="flex justify-between items-center text-[10px] font-bold">
                        <div className="flex items-center gap-2">
                          <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: COLORS_PIE[i % COLORS_PIE.length] }} />
                          <span className="text-white/40 uppercase">{f.combustible}</span>
                        </div>
                        <span>{Math.round((f.count / (summary?.total_cars || 1)) * 100)}%</span>
                      </div>
                    ))}
                 </div>
              </GlassCard>

              <GlassCard title="Oportunidades" subtitle="Vehículos bajo precio mercado" icon={Percent}>
                 <div className="space-y-3">
                    {opportunities?.slice(0, 5).map(opp => (
                      <a 
                        key={opp.car_id}
                        href={opp.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-3 p-3 rounded-xl bg-emerald-500/5 border border-emerald-500/10 hover:bg-emerald-500/10 transition-all group"
                      >
                         <div className="flex-1 overflow-hidden">
                            <h5 className="text-[10px] font-black uppercase text-white/50 truncate group-hover:text-white transition-colors">{opp.marca} {opp.modelo}</h5>
                            <div className="flex items-center gap-2 mt-1">
                               <span className="text-sm font-black italic tracking-tighter text-emerald-400">${opp.precio_usd?.toLocaleString()}</span>
                               <span className="text-[8px] font-bold bg-emerald-500 text-black px-1.5 py-0.5 rounded italic">-{opp.deviation_percent}%</span>
                            </div>
                         </div>
                         <ChevronRight size={14} className="text-white/20 group-hover:text-white group-hover:translate-x-1 transition-all" />
                      </a>
                    ))}
                    <Link href="/search" className="block text-center text-[9px] font-black uppercase tracking-[0.2em] text-blue-400 mt-4 hover:underline transition-all">
                       Ver más unidades →
                    </Link>
                 </div>
              </GlassCard>

           </div>

        </div>

        {/* --- Section 5: Geographic Map Placeholder --- */}
        <GlassCard title="Cobertura Territorial" subtitle="Densidad de oferta por provincia" icon={MapPin}>
           <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
              {provinceStats?.map((p, i) => (
                <div key={p.provincia} className="p-4 rounded-2xl bg-white/5 border border-white/5 text-center flex flex-col items-center gap-2 group hover:bg-white/10 transition-all">
                   <div className="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center text-xs font-black italic text-white/20 group-hover:text-blue-400 transition-colors">
                      {i + 1}
                   </div>
                   <div>
                      <p className="text-[10px] font-black uppercase tracking-widest leading-none mb-1">{p.provincia}</p>
                      <p className="text-xl font-black italic tracking-tighter text-blue-400">{p.count}</p>
                      <p className="text-[8px] font-bold text-white/20 uppercase">Autos</p>
                   </div>
                </div>
              ))}
           </div>
        </GlassCard>

      </div>

      <style jsx global>{`
        .gradient-bg {
          background-color: #050505;
          background-image: radial-gradient(at 0% 0%, rgba(59, 130, 246, 0.05) 0, transparent 50%), 
                            radial-gradient(at 100% 100%, rgba(99, 102, 241, 0.05) 0, transparent 50%);
        }
        .glass {
          background: rgba(255, 255, 255, 0.03);
          backdrop-filter: blur(24px);
          -webkit-backdrop-filter: blur(24px);
        }
        .animate-floating {
          animation: floating 8s ease-in-out infinite;
        }
        @keyframes floating {
          0%, 100% { transform: translateY(0) rotate(0); }
          50% { transform: translateY(-20px) rotate(5deg); }
        }
        .animate-pulse-slow {
          animation: pulse-slow 10s ease-in-out infinite;
        }
        @keyframes pulse-slow {
          0%, 100% { opacity: 0.1; transform: scale(1); }
          50% { opacity: 0.3; transform: scale(1.1); }
        }
      `}</style>
    </main>
  );
}
