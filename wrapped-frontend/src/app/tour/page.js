"use client"
import { getApiBaseUrl, robustFetcher as fetcher } from '@/lib/api';
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  BarChart3 as BarChart, 
  TrendingUp, 
  Car, 
  ChevronRight, 
  ChevronLeft, 
  Zap, 
  Fuel, 
  Search, 
  Calendar,
  Key,
  Navigation,
  Flag,
  Settings2,
  X,
  MapPin,
  Award,
  Crown,
  MousePointer2
} from 'lucide-react';
import Link from 'next/link';
import { cn } from '@/lib/utils';
import confetti from 'canvas-confetti';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { useTheme } from '@/context/ThemeContext';

const SLIDES = [
  'global-stats',
  'market-leaders',
  'provinces',
  'curiosities',
  'fuel-stats',
  'years-dist',
  'transmission-stats',
  'opportunities',
  'brand-selection',
  'model-selection',
  'verdict'
];

const THEMES = {
  'global-stats': 'from-blue-900 to-indigo-950',
  'market-leaders': 'from-blue-900 to-indigo-950',
  provinces: 'from-indigo-900 to-purple-950',
  curiosities: 'from-indigo-900 to-purple-950',
  'fuel-stats': 'from-purple-900 to-violet-950',
  'years-dist': 'from-purple-900 to-violet-950',
  'transmission-stats': 'from-purple-900 to-violet-950',
  opportunities: 'from-emerald-900 to-teal-950',
  'brand-selection': 'from-zinc-900 to-black',
  'model-selection': 'from-zinc-900 to-black',
  verdict: 'from-blue-900 to-black',
};

const AUTO_ADVANCE_DURATION = 6000;

export default function WrappedStory() {
  const { theme: appTheme } = useTheme();
  const [currentSlideIndex, setCurrentSlideIndex] = useState(0);
  const [direction, setDirection] = useState(1);
  const [globalStats, setGlobalStats] = useState(null);
  const [curiosities, setCuriosities] = useState(null);
  const [fuelStats, setFuelStats] = useState([]);
  const [brands, setBrands] = useState([]);
  const [isPaused, setIsPaused] = useState(false);
  const [userChoice, setUserChoice] = useState({ marca: null, modelo: null, combustible: null });
  const [models, setModels] = useState([]);
  const [verdict, setVerdict] = useState(null);
  const [loading, setLoading] = useState(false);
  const [opportunities, setOpportunities] = useState([]);

  useEffect(() => {
    async function fetchData() {
      const baseUrl = getApiBaseUrl();
      try {
        const [summaryData, curiosData, brandsData, fuelData, oppData] = await Promise.all([
          fetcher(`${baseUrl}/api/insights/summary`),
          fetcher(`${baseUrl}/api/insights/curiosities`),
          fetcher(`${baseUrl}/api/insights/brands`),
          fetcher(`${baseUrl}/api/insights/distribution/fuel`),
          fetcher(`${baseUrl}/api/insights/opportunities`)
        ]);
        
        if (summaryData) setGlobalStats(summaryData);
        if (curiosData) setCuriosities(curiosData);
        if (brandsData) setBrands(brandsData);
        if (fuelData) setFuelStats(fuelData);
        if (oppData) setOpportunities(oppData);
      } catch (error) {
        console.error("Error fetching data:", error);
      }
    }
    fetchData();
  }, []);

  const provinceStats = useMemo(() => {
    if (!globalStats?.by_province) return [];
    return Object.entries(globalStats.by_province)
      .map(([provincia, count]) => ({ provincia, count }))
      .sort((a,b) => b.count - a.count);
  }, [globalStats]);

  const yearStats = useMemo(() => {
    if (!globalStats?.by_year) return [];
    return Object.entries(globalStats.by_year)
      .map(([año, count]) => ({ año, count }))
      .sort((a,b) => b.año - a.año);
  }, [globalStats]);

  const transmissionStats = useMemo(() => {
    if (!globalStats?.by_transmission) return [];
    return Object.entries(globalStats.by_transmission)
      .map(([transmisión, count]) => ({ transmisión, count }))
      .sort((a,b) => b.count - a.count);
  }, [globalStats]);

  const nextSlide = useCallback(() => {
    if (currentSlideIndex < SLIDES.length - 1) {
      setDirection(1);
      setCurrentSlideIndex(prev => prev + 1);
    }
  }, [currentSlideIndex]);

  const prevSlide = () => {
    if (currentSlideIndex > 0) {
      setDirection(-1);
      setCurrentSlideIndex(prev => prev - 1);
    }
  };

  useEffect(() => {
    const currentSlide = SLIDES[currentSlideIndex];
    if (['brand-selection', 'model-selection', 'verdict'].includes(currentSlide) || isPaused) return;
    const timer = setTimeout(() => nextSlide(), AUTO_ADVANCE_DURATION);
    return () => clearTimeout(timer);
  }, [currentSlideIndex, isPaused, nextSlide]);

  const handleBrandSelect = async (marca) => {
    setUserChoice(prev => ({ ...prev, marca }));
    const baseUrl = getApiBaseUrl();
    const data = await fetcher(`${baseUrl}/api/insights/models?brand=${marca}`);
    setModels(data || []);
    nextSlide();
  };

  const handleModelSelect = (modelo) => {
    setUserChoice(prev => ({ ...prev, modelo }));
  };

  const handleVerdictFetch = async (combustible) => {
    setLoading(true);
    nextSlide();
    const baseUrl = getApiBaseUrl();
    try {
      const data = await fetcher(`${baseUrl}/api/insights/verdict?brand=${userChoice.marca}&model=${userChoice.modelo}&fuel=${combustible}`);
      setVerdict(data);
      confetti({ particleCount: 150, spread: 70, origin: { y: 0.6 }, colors: ['#06b6d4', '#3b82f6', '#10b981'] });
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const currentThemeClassName = useMemo(() => {
    const slide = SLIDES[currentSlideIndex];
    return THEMES[slide] || 'from-zinc-900 to-black';
  }, [currentSlideIndex]);

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: { staggerChildren: 0.1 } }
  };

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: { y: 0, opacity: 1 }
  };

  return (
    <main 
      className={cn(
        "h-screen w-full flex items-center justify-center transition-all duration-1000 bg-gradient-to-br overflow-hidden relative font-sans",
        currentThemeClassName
      )}
      onMouseDown={() => setIsPaused(true)}
      onMouseUp={() => setIsPaused(false)}
    >
      <Link
        href="/"
        className="absolute top-6 right-6 z-50 p-3 bg-white/10 hover:bg-white/20 border border-white/20 rounded-full transition-all text-white backdrop-blur-md"
      >
        <X size={24} />
      </Link>

      {/* Kinetic Background Elements */}
      <div className="absolute inset-0 z-0 overflow-hidden pointer-events-none opacity-20">
        <motion.div animate={{ y: [0, -20, 0] }} transition={{ duration: 5, repeat: Infinity }} className="absolute top-[10%] left-[5%]"><Key size={100} /></motion.div>
        <motion.div animate={{ y: [0, 20, 0] }} transition={{ duration: 6, repeat: Infinity }} className="absolute bottom-[20%] right-[10%]"><Navigation size={120} /></motion.div>
        <div className="absolute top-[30%] right-[10%] animate-floating opacity-5 delay-700"><Navigation size={120} className="text-white" /></div>
        <div className="absolute bottom-[20%] left-[15%] animate-floating opacity-10 delay-1000"><Flag size={64} className="text-white" /></div>
        <div className="absolute bottom-[10%] right-[20%] animate-floating opacity-5 delay-500"><Settings2 size={100} className="text-white" /></div>
        <div className="absolute top-[50%] left-[40%] animate-pulse-slow opacity-20"><Zap size={200} className="text-cyan-500" /></div>
      </div>

      <div className="w-full max-w-lg h-full max-h-[90vh] relative z-10 mx-4 flex flex-col">
        {/* Progress Bar */}
        <div className="flex gap-1 mb-8">
           {SLIDES.map((_, i) => (
             <div key={i} className="h-1 flex-1 bg-white/10 rounded-full overflow-hidden">
                <motion.div 
                  initial={{ width: 0 }}
                  animate={{ width: i <= currentSlideIndex ? '100%' : '0%' }}
                  className="h-full bg-cyan-400"
                />
             </div>
           ))}
        </div>

        <AnimatePresence mode="wait" custom={direction}>
          <motion.div
            key={currentSlideIndex}
            custom={direction}
            initial={{ opacity: 0, x: direction * 50 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -direction * 50 }}
            className="flex-1 flex flex-col"
          >
            {currentSlideIndex === 0 && (
              <Card className="flex-1 flex flex-col justify-center text-center gap-6" hover={false}>
                <div className="w-24 h-24 bg-cyan-500/20 rounded-[2.5rem] flex items-center justify-center mx-auto border border-cyan-500/30">
                  <Car size={48} className="text-cyan-400" />
                </div>
                <h1 className="text-5xl font-black italic tracking-tighter text-white">
                  Crautos <br/><span className="text-cyan-400 text-glow">Wrapped</span>
                </h1>
                <p className="text-white/50">Tu historia con el mercado automotriz.</p>
                <Button variant="primary" onClick={nextSlide} size="lg" className="mx-auto mt-4">
                  DESCUBRIR <ChevronRight size={20} className="ml-2" />
                </Button>
                <Link href="/" className="text-xs font-bold text-white/30 uppercase tracking-widest hover:text-white transition-colors">Volver al inicio</Link>
              </Card>
            )}

            {currentSlideIndex === 1 && (
              <Card className="flex-1 flex flex-col justify-center gap-8" hover={false}>
                <TrendingUp size={64} className="text-cyan-400" />
                <h2 className="text-4xl font-black italic text-white uppercase leading-none">El mercado <br/>está vibrando.</h2>
                <div className="space-y-4">
                   <div className="p-6 rounded-3xl bg-white/5 border border-white/10">
                      <p className="text-[10px] font-black uppercase text-white/30 tracking-widest mb-1">Total Autos</p>
                      <p className="text-5xl font-black text-cyan-400 font-mono tracking-tighter">{globalStats?.total_cars?.toLocaleString()}</p>
                   </div>
                </div>
              </Card>
            )}

            {currentSlideIndex === 2 && (
              <Card className="flex-1 flex flex-col justify-center gap-6" hover={false}>
                <MapPin size={64} className="text-cyan-400" />
                <h2 className="text-4xl font-black italic text-white leading-none">Concentración <br/><span className="text-cyan-400 text-glow">Geográfica</span></h2>
                <div className="space-y-3 overflow-y-auto max-h-[50vh] pr-2">
                   {provinceStats.slice(0, 4).map(p => (
                      <div key={p.provincia} className="p-4 rounded-2xl bg-white/5 border border-white/10 flex justify-between items-center group hover:bg-cyan-600 transition-colors">
                         <p className="font-bold text-lg">{p.provincia}</p>
                         <div className="text-right">
                            <p className="font-mono font-bold text-cyan-400 group-hover:text-white">{p.count} autos</p>
                            <p className="text-[10px] text-white/20 uppercase font-bold group-hover:text-white/60">En el mapa</p>
                         </div>
                      </div>
                   ))}
                </div>
              </Card>
            )}

            {currentSlideIndex === 3 && (
              <Card className="flex-1 flex flex-col justify-center gap-6" hover={false}>
                <BarChart size={64} className="text-cyan-400" />
                <h2 className="text-3xl font-black italic text-white uppercase leading-none">Hallazgos únicos</h2>
                <div className="grid gap-3 mt-4">
                  {curiosities && (
                    <>
                      <div className="p-4 rounded-2xl bg-gradient-to-r from-cyan-900/40 to-transparent border border-cyan-500/30">
                        <p className="text-[10px] text-cyan-400 font-black uppercase tracking-wider">Lujo Extremo</p>
                        <p className="text-lg font-black truncate text-white">{curiosities.most_expensive?.title}</p>
                        <p className="text-xs text-white/50 font-mono">${curiosities.most_expensive?.precio_usd.toLocaleString()}</p>
                      </div>
                      <div className="p-4 rounded-2xl bg-gradient-to-r from-emerald-900/40 to-transparent border border-emerald-500/30">
                        <p className="text-[10px] text-emerald-400 font-black uppercase tracking-wider">Ahorro Máximo</p>
                        <p className="text-lg font-black truncate text-white">{curiosities.cheapest?.title}</p>
                        <p className="text-xs text-white/50 font-mono">${curiosities.cheapest?.precio_usd.toLocaleString()}</p>
                      </div>
                    </>
                  )}
                </div>
              </Card>
            )}

            {currentSlideIndex === 4 && (
              <Card className="flex-1 flex flex-col justify-center gap-6" hover={false}>
                <Fuel size={64} className="text-purple-400" />
                <h2 className="text-3xl font-black italic text-white leading-none">¿Qué mueve a <br/><span className="text-purple-400">Costa Rica?</span></h2>
                <div className="space-y-4">
                  {fuelStats.slice(0, 3).map((f) => (
                    <div key={f.combustible} className="relative p-5 rounded-2xl bg-white/5 border border-white/10 overflow-hidden group">
                      <motion.div initial={{ width: 0 }} animate={{ width: `${(f.count / globalStats?.total_cars) * 100}%` }} transition={{ duration: 1.5 }} className="absolute top-0 left-0 h-full bg-purple-500/20" />
                      <div className="relative flex justify-between items-center">
                        <p className="font-black text-lg group-hover:text-purple-300 transition-colors uppercase tracking-tight">{f.combustible}</p>
                        <p className="text-purple-400 font-mono font-black">{Math.round((f.count / globalStats?.total_cars) * 100)}%</p>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            )}

            {currentSlideIndex === 5 && (
              <Card className="flex-1 flex flex-col justify-center gap-6" hover={false}>
                <Calendar size={64} className="text-purple-400" />
                <h2 className="text-4xl font-black italic text-white tracking-tighter leading-none">Años de <br/><span className="text-purple-400">Evolución</span></h2>
                <div className="flex h-40 items-end gap-1 px-2 border-b border-white/10 mt-6">
                   {yearStats.slice(0, 15).reverse().map((y, idx) => (
                      <motion.div 
                        key={y.año} 
                        initial={{ height: 0 }}
                        animate={{ height: `${(y.count / Math.max(...yearStats.map(ys => ys.count))) * 100}%` }}
                        transition={{ duration: 0.8, delay: idx * 0.05 }}
                        className="flex-1 bg-purple-500/40 rounded-t-lg transition-all hover:bg-purple-500 hover:scale-110 group relative"
                      >
                         <div className="absolute -top-10 left-1/2 -translate-x-1/2 bg-white text-black text-[8px] font-black px-1 rounded opacity-0 group-hover:opacity-100 transition-opacity">
                            {y.año}
                         </div>
                      </motion.div>
                   ))}
                </div>
                <p className="text-center text-[10px] text-white/30 uppercase font-black tracking-widest mt-2">{yearStats[14]?.año} ← Tiempo → {yearStats[0]?.año}</p>
              </Card>
            )}

            {currentSlideIndex === 6 && (
              <Card className="flex-1 flex flex-col justify-center gap-10" hover={false}>
                <MousePointer2 size={64} className="text-purple-400" />
                <h2 className="text-4xl font-black italic text-white leading-none uppercase tracking-tighter">¿Manual o <br /><span className="text-purple-400">Automático?</span></h2>
                <div className="flex items-center gap-1 h-12 rounded-2xl overflow-hidden border border-white/10 p-1 bg-white/5">
                   {transmissionStats.slice(0,2).map((t, i) => (
                      <motion.div key={t.transmisión} initial={{ width: 0 }} animate={{ width: `${(t.count / (transmissionStats[0]?.count + transmissionStats[1]?.count)) * 100}%` }} transition={{ duration: 1.2 }} className={cn("h-full flex items-center justify-center transition-all", i === 0 ? "bg-purple-600 shadow-[0_0_15px_rgba(147,51,234,0.4)]" : "bg-white/10")}>
                         <p className="text-[10px] font-black uppercase text-center px-2 truncate">{t.transmisión}</p>
                      </motion.div>
                   ))}
                </div>
                <p className="text-sm text-white/40 italic text-center">&quot;La comodidad parece estar ganando la carrera en las calles ticas.&quot;</p>
              </Card>
            )}

            {currentSlideIndex === 7 && (
              <Card className="flex-1 flex flex-col justify-center gap-6" hover={false}>
                <Award size={64} className="text-emerald-400" />
                <h2 className="text-3xl font-black italic text-emerald-400 uppercase leading-none">Oportunidades <br/><span className="text-white">Relámpago</span></h2>
                <div className="flex-1 overflow-y-auto max-h-[50vh] space-y-3 pr-2 mt-4">
                  {opportunities.slice(0, 5).map(o => (
                    <div key={o.car_id} className="p-4 rounded-xl bg-white/5 border border-white/10 flex justify-between items-center group hover:bg-emerald-600 transition-colors">
                      <div>
                        <p className="font-black text-sm tracking-tight capitalize">{o.marca} {o.modelo}</p>
                        <p className="text-xs text-emerald-400 font-bold group-hover:text-white">-{o.deviation_percent}% bajo el promedio</p>
                      </div>
                      <div className="text-right">
                        <p className="font-mono font-bold text-emerald-400 group-hover:text-white">${o.precio_usd.toLocaleString()}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            )}

            {currentSlideIndex === 8 && (
              <Card className="flex-1 flex flex-col pt-8 gap-6" hover={false}>
                <h2 className="text-3xl font-black italic text-white leading-none">Tu turno. <br/>¿Qué marca te interesa?</h2>
                <div className="flex-1 overflow-y-auto pr-2 grid grid-cols-2 gap-3">
                  {brands.slice(0, 12).map((b) => (
                    <button key={b.marca} onClick={() => handleBrandSelect(b.marca)} className="p-4 text-left rounded-2xl bg-white/5 border border-white/10 hover:bg-cyan-600 transition-all group flex flex-col justify-between active:scale-95">
                      <p className="font-black text-lg group-hover:text-white uppercase leading-none tracking-tighter">{b.marca}</p>
                      <p className="text-[10px] text-white/30 group-hover:text-white/60 font-black uppercase mt-2">{b.count} unidades</p>
                    </button>
                  ))}
                </div>
              </Card>
            )}

            {currentSlideIndex === 9 && (
              <Card className="flex-1 flex flex-col pt-8 gap-6" hover={false}>
                <div>
                  <h2 className="text-3xl font-black italic text-white leading-none mb-2">Escogiste <span className="text-cyan-400 uppercase tracking-tighter">{userChoice.marca}</span></h2>
                  <p className="text-white/40 font-bold uppercase tracking-widest text-[10px]">¿Cuál es el modelo que buscas?</p>
                </div>
                <div className="flex-1 overflow-y-auto pr-2 grid grid-cols-1 gap-2">
                  {models.map((m) => (
                    <button key={m} onClick={() => handleModelSelect(m)} className={cn("p-4 text-left rounded-xl transition-all border font-black uppercase tracking-tight active:scale-[0.98]", userChoice.modelo === m ? "bg-cyan-600 border-cyan-400 scale-[1.02] shadow-[0_0_20px_rgba(6,182,212,0.4)]" : "bg-white/5 border-white/10 hover:bg-white/10")}>
                      {m}
                    </button>
                  ))}
                </div>
                {userChoice.modelo && (
                  <div className="pt-4 border-t border-white/10 space-y-4">
                    <p className="text-[10px] font-black text-white/40 uppercase tracking-[0.2em] text-center">Tipo de combustible</p>
                    <div className="flex gap-2">
                       {['Gasolina', 'Diésel', 'Eléctrico'].map(f => (
                         <Button variant="secondary" key={f} onClick={() => handleVerdictFetch(f)} className="flex-1 py-3 text-xs">{f}</Button>
                       ))}
                    </div>
                  </div>
                )}
              </Card>
            )}

            {currentSlideIndex === 10 && (
              <div className="flex-1 flex flex-col justify-center space-y-8">
                {loading ? (
                  <div className="text-center space-y-4">
                    <motion.div animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: "linear" }} className="w-12 h-12 border-4 border-cyan-500 border-t-transparent rounded-full mx-auto" />
                    <p className="text-white/50 font-black uppercase tracking-widest text-xs">Calculando veredicto...</p>
                  </div>
                ) : verdict ? (
                  <motion.div initial={{ opacity: 0, scale: 0.9, y: 20 }} animate={{ opacity: 1, scale: 1, y: 0 }} className="space-y-6">
                    <Card className="p-8 bg-black/40 backdrop-blur-xl border-white/5" hover={false}>
                       <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/20 text-cyan-400 text-[10px] font-black uppercase tracking-[0.2em] mb-4">
                         <Zap size={14} /> El Veredicto Final
                       </div>
                       <h2 className="text-4xl font-black leading-tight tracking-tighter italic mb-4">
                         {userChoice.marca} {userChoice.modelo} <br />
                         <span className="text-cyan-400">#MarketReady</span>
                       </h2>
                       <p className="text-lg text-white/80 leading-snug italic font-medium mb-6">
                         &quot;{verdict.verdict_text || "Un modelo con gran presencia en el mercado costarricense."}&quot;
                       </p>
                       <div className="grid grid-cols-2 gap-4 pt-6 border-t border-white/10">
                          <div>
                             <p className="text-[10px] text-white/30 uppercase font-black">Precio Estimado</p>
                             <p className="text-2xl font-black font-mono text-green-400 italic">${verdict.avg_price_usd?.toLocaleString()}</p>
                          </div>
                          <div className="text-right">
                             <p className="text-[10px] text-white/30 uppercase font-black">Cuota Mercado</p>
                             <p className="text-2xl font-black font-mono text-cyan-400 italic">{(verdict.market_share_percent * 100).toFixed(1)}%</p>
                          </div>
                       </div>
                    </Card>
                    <div className="flex flex-col gap-3">
                      <Button variant="primary" size="lg" className="gap-2" onClick={() => window.location.href='/search'}>
                        <Search size={18} /> Explorar este modelo ahora
                      </Button>
                      <Button variant="ghost" onClick={() => setCurrentSlideIndex(0)} className="text-white/30 uppercase tracking-widest text-xs">Reiniciar historia</Button>
                    </div>
                  </motion.div>
                ) : (
                  <Card className="text-center p-8">Error al procesar. Reintenta.</Card>
                )}
              </div>
            )}
          </motion.div>
        </AnimatePresence>

        {/* Navigation Layers */}
        <div className="absolute inset-0 flex z-30 pointer-events-none">
           <div className="w-1/2 h-full cursor-w-resize pointer-events-auto" onClick={prevSlide} />
           <div className="w-1/2 h-full cursor-e-resize pointer-events-auto" onClick={nextSlide} />
        </div>
      </div>
    </main>
  );
}
