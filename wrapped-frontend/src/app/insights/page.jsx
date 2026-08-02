"use client"
import React, { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
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
  DollarSign,
  Gauge,
  Car,
  ChevronRight,
} from 'lucide-react';
import useSWR from 'swr';
import { useTheme } from '@/context/ThemeContext';
import { cn } from '@/lib/utils';
import { getApiBaseUrl, robustFetcher as fetcher } from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Background } from '@/components/layout/Background';
import { PageHeader } from '@/components/layout/PageHeader';

export default function InsightsDashboard() {
  const { theme } = useTheme();
  const baseUrl = getApiBaseUrl();
  
  // Data Fetching
  const { data: summary } = useSWR(`${baseUrl}/api/insights/summary`, fetcher);
  const { data: curiosities } = useSWR(`${baseUrl}/api/insights/curiosities`, fetcher);
  const { data: opportunities } = useSWR(`${baseUrl}/api/insights/opportunities`, fetcher);
  const { data: depreciation } = useSWR(`${baseUrl}/api/insights/depreciation`, fetcher);
  const { data: ratiosData } = useSWR(`${baseUrl}/api/insights/ratios/top`, fetcher);
  const { data: fuelStats } = useSWR(`${baseUrl}/api/insights/distribution/fuel`, fetcher);
  const { data: provinceStats } = useSWR(`${baseUrl}/api/insights/provinces`, fetcher);
  const { data: explorerData } = useSWR(`${baseUrl}/api/insights/explorer`, fetcher);

  const bestValueRatios = useMemo(() => {
    if (!Array.isArray(ratiosData)) return [];
    return [...ratiosData].sort((a, b) => a.ratio_usd - b.ratio_usd).slice(0, 10);
  }, [ratiosData]);

  const [selectedBrands, setSelectedBrands] = useState(['Toyota', 'Hyundai', 'Nissan']);
  const depreciationChartData = useMemo(() => {
    if (!Array.isArray(depreciation)) return [];
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

  const [scatterX, setScatterX] = useState('año');
  const [scatterY, setScatterY] = useState('precio_usd');
  const [scatterColor, setScatterColor] = useState('transmisión');

  const COLORS_PIE = ['#06b6d4', '#8b5cf6', '#10b981', '#f59e0b', '#f43f5e', '#6366f1', '#ec4899'];
  const cardVariant = theme === 'dark' ? 'glass' : 'white';
  const axisColor = theme === 'dark' ? 'rgba(255,255,255,0.3)' : 'rgba(15,23,42,0.4)';
  const gridColor = theme === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(15,23,42,0.08)';
  const tooltipStyle = theme === 'dark'
    ? { backgroundColor: '#111', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '1rem', fontSize: '12px', color: '#fff' }
    : { backgroundColor: '#fff', border: '1px solid rgba(15,23,42,0.1)', borderRadius: '1rem', fontSize: '12px', color: '#0f172a' };

  return (
    <main className="min-h-screen w-full relative pb-20">
      <Background />

      <PageHeader
        title="MARKET"
        accent="INSIGHTS"
        subtitle="Dash Application Analytics V2"
        actions={
          <div className="flex items-center gap-4">
            <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-2xl flex items-center gap-3">
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-[10px] font-black uppercase text-emerald-500 dark:text-emerald-400 tracking-widest">Live Integration</span>
            </div>
          </div>
        }
      />

      <div className="max-w-[1400px] mx-auto px-6 py-12 space-y-10 relative z-10">
        
        {/* Banner Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
           {[
             { label: 'Muestra', val: summary?.total_cars?.toLocaleString(), icon: Car, color: 'text-cyan-400', bg: 'bg-cyan-600/20' },
             { label: 'Promedio', val: `$${summary?.avg_price_usd?.toLocaleString()}`, icon: DollarSign, color: 'text-emerald-400', bg: 'bg-emerald-600/20' },
             { label: 'Uso Medio', val: '84.2K KM', icon: Gauge, color: 'text-indigo-400', bg: 'bg-indigo-600/20' },
             { label: 'Tendencia', val: '+12.4%', icon: TrendingUp, color: 'text-purple-400', bg: 'bg-purple-600/20' },
           ].map((stat, i) => (
             <Card key={i} variant={cardVariant} className="p-7 flex flex-col gap-4">
                <div className={cn("w-12 h-12 rounded-2xl flex items-center justify-center", stat.bg, stat.color)}>
                  <stat.icon size={24} />
                </div>
                <div>
                   <p className="text-[10px] font-black text-slate-400 dark:text-white/30 uppercase tracking-widest italic mb-1">{stat.label}</p>
                   <h2 className="text-4xl font-black italic tracking-tighter leading-none text-slate-900 dark:text-white">{stat.val || '...'}</h2>
                </div>
             </Card>
           ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-[1fr_350px] gap-10">

           <div className="space-y-10">
              <Card variant={cardVariant} className="p-8" hover={false}>
                 <div className="flex items-center gap-4 mb-8">
                    <div className="w-10 h-10 rounded-2xl bg-cyan-600/20 flex items-center justify-center text-cyan-400"><TrendingUp size={20} /></div>
                    <h3 className="text-xs font-black uppercase tracking-[0.2em] text-slate-900 dark:text-white">Análisis de Depreciación</h3>
                 </div>
                 <div className="flex flex-wrap gap-2 mb-8">
                    {['Toyota', 'Hyundai', 'Nissan', 'Kia', 'Suzuki'].map(brand => (
                      <Button
                        key={brand}
                        variant={selectedBrands.includes(brand) ? 'primary' : 'secondary'}
                        onClick={() => setSelectedBrands(prev => prev.includes(brand) ? prev.filter(b => b !== brand) : [...prev, brand])}
                        className="text-[10px] px-4 py-2"
                      >
                        {brand}
                      </Button>
                    ))}
                 </div>
                 <div className="h-[400px]">
                    <ResponsiveContainer width="100%" height="100%">
                       <LineChart data={depreciationChartData}>
                          <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
                          <XAxis dataKey="name" stroke={axisColor} fontSize={10} axisLine={false} tickLine={false} />
                          <YAxis stroke={axisColor} fontSize={10} axisLine={false} tickLine={false} tickFormatter={(v) => `$${v/1000}k`} />
                          <Tooltip contentStyle={tooltipStyle} />
                          <Legend wrapperStyle={{ fontSize: '10px', paddingTop: '20px', color: axisColor }} />
                          {selectedBrands.map((brand, i) => (
                            <Line key={brand} type="monotone" dataKey={brand} stroke={COLORS_PIE[i % COLORS_PIE.length]} strokeWidth={3} dot={false} />
                          ))}
                       </LineChart>
                    </ResponsiveContainer>
                 </div>
              </Card>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <Card variant={cardVariant} className="p-6" hover={false}>
                   <h3 className="text-xs font-black uppercase tracking-widest mb-6 text-slate-900 dark:text-white">Mejor Relación $/KM</h3>
                   <div className="h-[300px]">
                      <ResponsiveContainer width="100%" height="100%">
                         <BarChart data={bestValueRatios} layout="vertical">
                           <YAxis dataKey="modelo" type="category" stroke={axisColor} fontSize={9} width={90} axisLine={false} tickLine={false} />
                           <Bar dataKey="ratio_usd" fill="#06b6d4" radius={[0, 10, 10, 0]} barSize={20} />
                         </BarChart>
                      </ResponsiveContainer>
                   </div>
                </Card>
                <Card variant={cardVariant} className="p-6" hover={false}>
                   <h3 className="text-xs font-black uppercase tracking-widest mb-6 text-slate-900 dark:text-white">Oportunidades</h3>
                   <div className="space-y-3">
                      {opportunities?.slice(0, 5).map(opp => (
                        <a key={opp.car_id} href={opp.url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-3 p-3 rounded-xl bg-emerald-500/5 border border-emerald-500/10 hover:bg-emerald-500/10 group">
                           <div className="flex-1 overflow-hidden">
                              <h5 className="text-[10px] font-black uppercase text-slate-500 dark:text-white/50 truncate group-hover:text-slate-900 dark:group-hover:text-white">{opp.marca} {opp.modelo}</h5>
                              <span className="text-sm font-black italic text-emerald-600 dark:text-emerald-400">${opp.precio_usd?.toLocaleString()}</span>
                           </div>
                           <ChevronRight size={14} className="text-slate-300 dark:text-white/20 group-hover:text-emerald-500 dark:group-hover:text-emerald-400" />
                        </a>
                      ))}
                   </div>
                </Card>
              </div>
           </div>

           <div className="space-y-10">
              <Card variant={cardVariant} hover={false}>
                 <h3 className="text-xs font-black uppercase tracking-widest mb-6 text-slate-900 dark:text-white">Extremos</h3>
                 <div className="space-y-4">
                    {[
                      { l: 'Caro', v: curiosities?.most_expensive, p: 'price' },
                      { l: 'Barato', v: curiosities?.cheapest, p: 'price' },
                    ].map((ext, i) => (
                      <div key={i} className="p-4 rounded-2xl bg-slate-50 dark:bg-white/5 border border-slate-100 dark:border-white/5">
                        <p className="text-[9px] font-black text-cyan-600 dark:text-cyan-400 uppercase mb-1">{ext.l}</p>
                        <h4 className="font-bold text-sm truncate uppercase text-slate-900 dark:text-white">{ext.v?.marca} {ext.v?.modelo}</h4>
                        <p className="text-lg font-black italic mt-1 text-slate-900 dark:text-white">${ext.v?.precio_usd?.toLocaleString()}</p>
                      </div>
                    ))}
                 </div>
              </Card>

              <Card variant={cardVariant} hover={false}>
                 <h3 className="text-xs font-black uppercase tracking-widest mb-6 text-slate-900 dark:text-white">Mercado</h3>
                 <div className="h-[200px]">
                    <ResponsiveContainer width="100%" height="100%">
                       <PieChart>
                          <Pie
                            data={fuelStats || []}
                            innerRadius={60}
                            outerRadius={80}
                            paddingAngle={5}
                            dataKey="count"
                            nameKey="combustible"
                          >
                            {(fuelStats || []).map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={COLORS_PIE[index % COLORS_PIE.length]} stroke="none" />
                            ))}
                          </Pie>
                          <Tooltip contentStyle={tooltipStyle} />
                       </PieChart>
                    </ResponsiveContainer>
                 </div>
              </Card>
           </div>
        </div>
      </div>
    </main>
  );
}
