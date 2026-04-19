"use client"
import { getApiBaseUrl, robustFetcher as fetcher } from '@/lib/api';
import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  BarChart3 as BarChart, 
  TrendingUp, 
  Car, 
  ChevronRight, 
  ChevronLeft, 
  CheckCircle2, 
  AlertCircle,
  Zap,
  DollarSign,
  Fuel,
  Award,
  Search,
  Timer,
  MousePointer2,
  Crown,
  MapPin,
  Calendar,
  Key,
  Navigation,
  Flag,
  Settings2
} from 'lucide-react';
import Link from 'next/link';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import confetti from 'canvas-confetti';

function cn(...inputs) {
  return twMerge(clsx(inputs));
}

// Slides Configuration
const SLIDES = [
  'welcome',
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
  welcome: 'from-blue-900 to-indigo-950',
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

// Variants for staggered entry
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1
    }
  }
};

const itemVariants = {
  hidden: { y: 20, opacity: 0 },
  visible: { y: 0, opacity: 1 }
};

export default function WrappedStory() {
  const [currentSlideIndex, setCurrentSlideIndex] = useState(0);
  const [direction, setDirection] = useState(1);
  const [globalStats, setGlobalStats] = useState(null);
  const [curiosities, setCuriosities] = useState(null);
  const [fuelStats, setFuelStats] = useState([]);
  const [transmissionStats, setTransmissionStats] = useState([]);
  const [provinceStats, setProvinceStats] = useState([]);
  const [yearStats, setYearStats] = useState([]);
  const [opportunities, setOpportunities] = useState([]);
  const [userChoice, setUserChoice] = useState({
    marca: '',
    modelo: '',
    combustible: ''
  });
  const [verdict, setVerdict] = useState(null);
  const [loading, setLoading] = useState(false);
  const [brands, setBrands] = useState([]);
  const [models, setModels] = useState([]);
  const [isPaused, setIsPaused] = useState(false);

  useEffect(() => {
    async function fetchData() {
      const baseUrl = getApiBaseUrl();
      try {
        const [summaryData, curiosData, brandsData, fuelData, oppData, provinceData, yearData, transData] = await Promise.all([
          fetcher(`${baseUrl}/api/insights/summary`),
          fetcher(`${baseUrl}/api/insights/curiosities`),
          fetcher(`${baseUrl}/api/insights/brands`),
          fetcher(`${baseUrl}/api/insights/distribution/fuel`),
          fetcher(`${baseUrl}/api/insights/opportunities`),
          fetcher(`${baseUrl}/api/insights/provinces`),
          fetcher(`${baseUrl}/api/insights/years`),
          fetcher(`${baseUrl}/api/insights/distribution/transmission`)
        ]);
        
        if (summaryData) setGlobalStats(summaryData);
        if (curiosData) setCuriosities(curiosData);
        if (brandsData) setBrands(brandsData);
        if (fuelData) setFuelStats(fuelData);
        if (oppData) setOpportunities(oppData);
        if (provinceData) setProvinceStats(provinceData);
        if (yearData) setYearStats(yearData);
        if (transData) setTransmissionStats(transData);
      } catch (error) {
        console.error("Error fetching data:", error);
      }
    }
    fetchData();
  }, []);

  const triggerConfetti = useCallback(() => {
    const duration = 3 * 1000;
    const animationEnd = Date.now() + duration;
    const defaults = { startVelocity: 30, spread: 360, ticks: 60, zIndex: 0 };
    const randomInRange = (min, max) => Math.random() * (max - min) + min;

    const interval = setInterval(function() {
      const timeLeft = animationEnd - Date.now();
      if (timeLeft <= 0) return clearInterval(interval);
      const particleCount = 50 * (timeLeft / duration);
      confetti({ ...defaults, particleCount, origin: { x: randomInRange(0.1, 0.3), y: Math.random() - 0.2 } });
      confetti({ ...defaults, particleCount, origin: { x: randomInRange(0.7, 0.9), y: Math.random() - 0.2 } });
    }, 250);
  }, []);

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

  const handleBrandSelect = (brand) => {
    setUserChoice(prev => ({ ...prev, marca: brand, modelo: '', combustible: '' }));
    const baseUrl = getApiBaseUrl();
    fetcher(`${baseUrl}/api/cars?marca=${brand}&limit=100`)
      .then(data => {
        if (data && data.cars) {
          const uniqueModels = [...new Set(data.cars.map(c => c.modelo))];
          setModels(uniqueModels);
          nextSlide();
        }
      });
  };

  const handleModelSelect = (model) => {
    setUserChoice(prev => ({ ...prev, modelo: model }));
    nextSlide();
  };

  const handleVerdictFetch = async (fuel) => {
    setLoading(true);
    setUserChoice(prev => ({ ...prev, combustible: fuel }));
    const baseUrl = getApiBaseUrl();
    try {
      const data = await fetcher(`${baseUrl}/api/insights/verdict?marca=${userChoice.marca}&modelo=${userChoice.modelo}&combustible=${fuel}`);
      if (data) {
        setVerdict(data);
        nextSlide();
        setTimeout(triggerConfetti, 500);
      }
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

  return (
    <main 
      className={cn(
        "h-screen w-full flex items-center justify-center transition-all duration-1000 bg-gradient-to-br overflow-hidden relative font-sans",
        currentThemeClassName
      )}
      onMouseDown={() => setIsPaused(true)}
      onMouseUp={() => setIsPaused(false)}
      onTouchStart={() => setIsPaused(true)}
      onTouchEnd={() => setIsPaused(false)}
    >
      {/* Kinetic Background Elements */}
      <div className="absolute inset-0 z-0 overflow-hidden pointer-events-none">
        <div className="absolute top-[10%] left-[5%] animate-floating opacity-10"><Key size={80} className="text-white" /></div>
        <div className="absolute top-[30%] right-[10%] animate-floating opacity-5 delay-700"><Navigation size={120} className="text-white" /></div>
        <div className="absolute bottom-[20%] left-[15%] animate-floating opacity-10 delay-1000"><Flag size={64} className="text-white" /></div>
        <div className="absolute bottom-[10%] right-[20%] animate-floating opacity-5 delay-500"><Settings2 size={100} className="text-white" /></div>
        <div className="absolute top-[50%] left-[40%] animate-pulse-slow opacity-20"><Zap size={200} className="text-blue-500" /></div>
      </div>

      <div className="w-full max-w-lg h-full max-h-[90vh] glass relative z-10 rounded-3xl p-8 flex flex-col shadow-2xl mx-4 overflow-hidden border border-white/10">
        {/* Story Progress Bars */}
        <div className="flex gap-1.5 absolute top-6 left-1/2 -translate-x-1/2 w-[85%] z-20">
          {SLIDES.map((_, i) => (
            <div key={i} className="h-1 flex-1 bg-white/10 rounded-full overflow-hidden">
               <motion.div 
                 initial={{ width: 0 }}
                 animate={{ 
                   width: i < currentSlideIndex ? '100%' : i === currentSlideIndex ? '100%' : '0%' 
                 }}
                 transition={{ 
                   duration: i === currentSlideIndex && !['brand-selection', 'model-selection', 'verdict'].includes(SLIDES[i]) && !isPaused ? AUTO_ADVANCE_DURATION/1000 : 0.4, 
                   ease: "linear" 
                 }}
                 className={cn(
                   "h-full rounded-full",
                   i <= currentSlideIndex ? "bg-white" : "bg-transparent"
                 )}
               />
            </div>
          ))}
        </div>

        <AnimatePresence mode="wait" custom={direction}>
          <motion.div
            key={currentSlideIndex}
            custom={direction}
            initial={{ opacity: 0, x: direction * 50, scale: 0.95 }}
            animate={{ opacity: 1, x: 0, scale: 1 }}
            exit={{ opacity: 0, x: -direction * 50, scale: 1.05 }}
            transition={{ duration: 0.5, ease: [0.23, 1, 0.32, 1] }}
            className="flex-1 flex flex-col justify-center gap-6 overflow-hidden pt-4"
          >
            {currentSlideIndex === 0 && (
              <div className="text-center space-y-6">
                <motion.div 
                  initial={{ rotate: -10, scale: 0 }}
                  animate={{ rotate: 0, scale: 1 }}
                  className="w-24 h-24 bg-blue-500/20 rounded-3xl flex items-center justify-center mx-auto mb-4 border border-blue-500/30 shadow-2xl shadow-blue-500/20"
                >
                  <Car size={48} className="text-blue-400" />
                </motion.div>
                <h1 className="text-5xl font-extrabold tracking-tight bg-gradient-to-br from-white to-white/60 bg-clip-text text-transparent italic leading-[1.1]">
                  Crautos <br/><span className="text-blue-400">Wrapped</span>
                </h1>
                <p className="text-lg text-white/50">Tu historia con el mercado automotriz en tiempo real</p>
                <div className="pt-8">
                   <p className="text-[10px] text-white/20 uppercase tracking-[0.3em] mb-4">Mantén presionado para pausar</p>
                    <button 
                    onClick={nextSlide}
                    className="w-full px-8 py-4 bg-blue-600 hover:bg-blue-500 rounded-full font-bold transition-all transform hover:scale-105 active:scale-95 shadow-lg shadow-blue-900/40 text-white"
                  >
                    Descubrir ahora
                  </button>
                  <Link 
                    href="/search"
                    className="w-full mt-4 px-8 py-4 bg-white/5 hover:bg-white/10 border border-white/10 rounded-full font-bold transition-all transform hover:scale-105 active:scale-95 flex items-center justify-center gap-3 group"
                  >
                    <Search size={20} className="text-blue-400 group-hover:scale-110 transition-transform" />
                    Market Explorer
                  </Link>
                  <Link 
                    href="/insights"
                    className="w-full mt-4 px-8 py-4 bg-blue-600/20 hover:bg-blue-600/30 border border-blue-500/30 rounded-full font-bold transition-all transform hover:scale-105 active:scale-95 flex items-center justify-center gap-3 group"
                  >
                    <TrendingUp size={20} className="text-blue-400 group-hover:scale-110 transition-transform" />
                    Market Insights Dashboard
                  </Link>
                </div>
              </div>
            )}

            {currentSlideIndex === 1 && (
              <motion.div variants={containerVariants} initial="hidden" animate="visible" className="space-y-8">
                <motion.div variants={itemVariants}><TrendingUp size={48} className="text-blue-400" /></motion.div>
                <motion.h2 variants={itemVariants} className="text-4xl font-bold leading-tight">El mercado está vibrando.</motion.h2>
                <div className="space-y-4">
                  <motion.div variants={itemVariants} className="p-6 rounded-2xl bg-white/5 border border-white/10 transition-transform hover:scale-[1.02]">
                    <p className="text-white/40 text-sm uppercase tracking-widest font-bold">Total de Autos</p>
                    <p className="text-5xl font-mono font-bold text-blue-400 tracking-tighter">{globalStats?.total_cars?.toLocaleString() || '...'}</p>
                  </motion.div>
                  <motion.div variants={itemVariants} className="p-6 rounded-2xl bg-white/5 border border-white/10 transition-transform hover:scale-[1.02]">
                    <p className="text-white/40 text-sm uppercase tracking-widest font-bold">Inversión Promedio</p>
                    <p className="text-5xl font-mono font-bold text-green-400 tracking-tighter">${globalStats?.avg_price_usd?.toLocaleString() || '...'}</p>
                  </motion.div>
                </div>
              </motion.div>
            )}

            {currentSlideIndex === 2 && (
              <motion.div variants={containerVariants} initial="hidden" animate="visible" className="space-y-8">
                <motion.div variants={itemVariants}><Crown size={48} className="text-yellow-400" /></motion.div>
                <motion.h2 variants={itemVariants} className="text-4xl font-black italic tracking-tighter leading-none">Los <span className="text-blue-400">Reyes</span> <br/>del Camino</motion.h2>
                <div className="space-y-3">
                  {brands.slice(0, 3).map((b, i) => (
                    <motion.div variants={itemVariants} key={b.marca} className="flex items-center gap-4 p-5 rounded-2xl bg-white/5 border border-white/10 relative overflow-hidden group hover:bg-white/10 transition-all">
                       <div className="text-2xl font-black text-white/10 italic">#{i+1}</div>
                       <div className="flex-1">
                         <p className="font-black text-xl uppercase italic leading-none group-hover:text-blue-400 transition-colors">{b.marca}</p>
                         <p className="text-xs text-white/30 uppercase font-bold mt-1">{b.count} unidades activas</p>
                       </div>
                    </motion.div>
                  ))}
                </div>
              </motion.div>
            )}

            {currentSlideIndex === 3 && (
              <motion.div variants={containerVariants} initial="hidden" animate="visible" className="space-y-6">
                <motion.div variants={itemVariants}><MapPin size={48} className="text-indigo-400" /></motion.div>
                <motion.h2 variants={itemVariants} className="text-4xl font-black italic tracking-tighter leading-none">Concentración <br/><span className="text-indigo-400">Geográfica</span></motion.h2>
                <div className="space-y-3">
                   {provinceStats.slice(0, 4).map(p => (
                      <motion.div variants={itemVariants} key={p.provincia} className="p-4 rounded-xl bg-white/5 border border-white/10 flex justify-between items-center group hover:bg-indigo-600 transition-colors">
                         <p className="font-bold text-lg">{p.provincia}</p>
                         <div className="text-right">
                            <p className="font-mono font-bold text-indigo-400 group-hover:text-white">{p.count} autos</p>
                            <p className="text-[10px] text-white/20 uppercase font-bold group-hover:text-white/60">En el mapa</p>
                         </div>
                      </motion.div>
                   ))}
                </div>
              </motion.div>
            )}

            {currentSlideIndex === 4 && (
              <motion.div variants={containerVariants} initial="hidden" animate="visible" className="space-y-6">
                <motion.div variants={itemVariants}><BarChart size={48} className="text-blue-400" /></motion.div>
                <motion.h2 variants={itemVariants} className="text-3xl font-bold italic">Hallazgos únicos...</motion.h2>
                <div className="grid gap-3">
                  {curiosities && (
                    <>
                      <motion.div variants={itemVariants} className="p-4 rounded-xl bg-gradient-to-r from-blue-900/40 to-transparent border border-blue-500/30 cursor-help">
                        <p className="text-[10px] text-blue-400 font-bold uppercase tracking-wider">Lujo Extremo</p>
                        <p className="text-lg font-bold truncate">{curiosities.most_expensive?.title}</p>
                        <p className="text-xs text-white/50">${curiosities.most_expensive?.precio_usd.toLocaleString()}</p>
                      </motion.div>
                      <motion.div variants={itemVariants} className="p-4 rounded-xl bg-gradient-to-r from-green-900/40 to-transparent border border-green-500/30 cursor-help">
                        <p className="text-[10px] text-green-400 font-bold uppercase tracking-wider">Ahorro Máximo</p>
                        <p className="text-lg font-bold truncate">{curiosities.cheapest?.title}</p>
                        <p className="text-xs text-white/50">${curiosities.cheapest?.precio_usd.toLocaleString()}</p>
                      </motion.div>
                    </>
                  )}
                </div>
              </motion.div>
            )}

            {currentSlideIndex === 5 && (
              <motion.div variants={containerVariants} initial="hidden" animate="visible" className="space-y-6">
                <motion.div variants={itemVariants}><Fuel size={48} className="text-purple-400" /></motion.div>
                <motion.h2 variants={itemVariants} className="text-3xl font-bold leading-tight">¿Qué mueve a <br/><span className="text-purple-400">Costa Rica?</span></motion.h2>
                <div className="space-y-3">
                  {fuelStats.slice(0, 3).map((f) => (
                    <motion.div variants={itemVariants} key={f.combustible} className="relative p-4 rounded-xl bg-white/5 border border-white/10 overflow-hidden group">
                      <motion.div 
                        initial={{ width: 0 }}
                        animate={{ width: `${(f.count / globalStats?.total_cars) * 100}%` }}
                        transition={{ duration: 1.5, ease: "easeOut" }}
                        className="absolute top-0 left-0 h-full bg-purple-500/20" 
                      />
                      <div className="relative flex justify-between items-center px-2">
                        <p className="font-bold text-lg group-hover:text-purple-300 transition-colors">{f.combustible}</p>
                        <p className="text-purple-400 font-mono font-bold">{Math.round((f.count / globalStats?.total_cars) * 100)}%</p>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </motion.div>
            )}

            {currentSlideIndex === 6 && (
              <motion.div variants={containerVariants} initial="hidden" animate="visible" className="space-y-6">
                <motion.div variants={itemVariants}><Calendar size={48} className="text-purple-400" /></motion.div>
                <motion.h2 variants={itemVariants} className="text-4xl font-black italic tracking-tighter leading-none">Años de <br/><span className="text-purple-400">Evolución</span></motion.h2>
                <div className="flex h-32 items-end gap-1 px-2 border-b border-white/10">
                   {yearStats.slice(0, 15).reverse().map((y, idx) => (
                      <motion.div 
                        key={y.año} 
                        initial={{ height: 0 }}
                        animate={{ height: `${(y.count / Math.max(...yearStats.map(ys => ys.count))) * 100}%` }}
                        transition={{ duration: 0.8, delay: idx * 0.05, ease: "backOut" }}
                        className="flex-1 bg-purple-500/40 rounded-t-lg transition-all hover:bg-purple-500 hover:scale-110 group relative"
                      >
                         <div className="absolute -top-10 left-1/2 -translate-x-1/2 bg-white text-black text-[8px] font-bold px-1 rounded opacity-0 group-hover:opacity-100 transition-opacity">
                            {y.año}: {y.count}
                         </div>
                      </motion.div>
                   ))}
                </div>
                <p className="text-center text-xs text-white/30 uppercase font-black tracking-widest mt-2">{yearStats[14]?.año} ← Tiempo → {yearStats[0]?.año}</p>
              </motion.div>
            )}

            {currentSlideIndex === 7 && (
              <motion.div variants={containerVariants} initial="hidden" animate="visible" className="space-y-10 py-10">
                <motion.div variants={itemVariants}><MousePointer2 size={48} className="text-purple-400" /></motion.div>
                <motion.h2 variants={itemVariants} className="text-4xl font-black leading-none uppercase tracking-tighter italic">
                   ¿Manual o <br /> <span className="text-purple-400">Automático?</span>
                </motion.h2>
                <motion.div variants={itemVariants} className="flex items-center gap-1 h-12 rounded-2xl overflow-hidden border border-white/10 p-1 bg-white/5">
                   {transmissionStats.slice(0,2).map((t, i) => (
                      <motion.div 
                        key={t.transmisión} 
                        initial={{ width: 0 }}
                        animate={{ width: `${(t.count / (transmissionStats[0]?.count + transmissionStats[1]?.count)) * 100}%` }}
                        transition={{ duration: 1.2, ease: "circOut" }}
                        className={cn(
                          "h-full flex items-center justify-center transition-all",
                          i === 0 ? "bg-purple-600 shadow-[0_0_15px_rgba(147,51,234,0.4)]" : "bg-white/10"
                        )}
                      >
                         <p className="text-[10px] font-black uppercase text-center px-2 truncate">{t.transmisión}</p>
                      </motion.div>
                   ))}
                </motion.div>
                <p className="text-sm text-white/40 italic text-center">&quot;La comodidad parece estar ganando la carrera en las calles ticas.&quot;</p>
              </motion.div>
            )}

            {currentSlideIndex === 8 && (
              <motion.div variants={containerVariants} initial="hidden" animate="visible" className="space-y-6">
                <motion.div variants={itemVariants}><Award size={48} className="text-emerald-400" /></motion.div>
                <motion.h2 variants={itemVariants} className="text-3xl font-bold leading-tight uppercase italic text-emerald-400">Oportunidades <br/><span className="text-white">Relámpago</span></motion.h2>
                <p className="text-white/50 italic text-sm">"Autos listados un 15% por debajo del promedio del mercado"</p>
                <div className="flex-1 overflow-y-auto max-h-[40vh] space-y-3 pr-2 custom-scrollbar">
                  {opportunities.slice(0, 5).map(o => (
                    <motion.div variants={itemVariants} key={o.car_id} className="p-4 rounded-xl bg-white/5 border border-white/10 flex justify-between items-center group hover:bg-emerald-600 transition-colors active:scale-95 duration-75">
                      <div>
                        <p className="font-bold text-sm tracking-tight capitalize">{o.marca} {o.modelo}</p>
                        <p className="text-xs text-emerald-400 font-bold group-hover:text-white">-{o.deviation_percent}% bajo el promedio</p>
                      </div>
                      <div className="text-right">
                        <p className="font-mono font-bold text-emerald-400 group-hover:text-white">${o.precio_usd.toLocaleString()}</p>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </motion.div>
            )}

            {currentSlideIndex === 9 && (
              <div className="flex-1 flex flex-col pt-8">
                <motion.h2 initial={{ y: -20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} className="text-3xl font-bold mb-6">Tu turno. <br/>¿Qué marca te interesa?</motion.h2>
                <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar grid grid-cols-2 gap-3">
                  {brands.slice(0, 12).map((b, idx) => (
                    <motion.button 
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: idx * 0.03 }}
                      key={b.marca} 
                      onClick={() => handleBrandSelect(b.marca)}
                      className="p-4 text-left rounded-2xl bg-white/5 border border-white/10 hover:bg-blue-600 transition-all hover:border-blue-400 group flex flex-col justify-between active:scale-95"
                    >
                      <p className="font-black text-lg group-hover:text-white uppercase leading-none tracking-tighter">{b.marca}</p>
                      <p className="text-[10px] text-white/30 group-hover:text-white/60 font-bold uppercase mt-2">{b.count} unidades</p>
                    </motion.button>
                  ))}
                </div>
              </div>
            )}

            {currentSlideIndex === 10 && (
              <div className="flex-1 flex flex-col pt-8 space-y-6">
                <motion.div initial={{ y: -20, opacity: 0 }} animate={{ y: 0, opacity: 1 }}>
                  <h2 className="text-3xl font-bold mb-2">Escogiste <span className="text-blue-400 uppercase italic tracking-tighter">{userChoice.marca}</span></h2>
                  <p className="text-white/40">¿Cuál es el modelo que buscas?</p>
                </motion.div>
                
                <div className="flex-1 overflow-y-auto pr-2 grid grid-cols-1 gap-2 custom-scrollbar">
                  {models.map((m, idx) => (
                    <motion.button 
                      initial={{ x: -20, opacity: 0 }}
                      animate={{ x: 0, opacity: 1 }}
                      transition={{ delay: idx * 0.02 }}
                      key={m} 
                      onClick={() => handleModelSelect(m)}
                      className={cn(
                        "p-4 text-left rounded-xl transition-all border font-bold uppercase tracking-tight active:scale-[0.98]",
                        userChoice.modelo === m ? "bg-blue-600 border-blue-400 scale-[1.02] shadow-[0_0_20px_rgba(37,99,235,0.4)]" : "bg-white/5 border-white/10 hover:bg-white/10"
                      )}
                    >
                      {m}
                    </motion.button>
                  ))}
                </div>

                {userChoice.modelo && (
                  <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} className="pt-4 border-t border-white/10 space-y-4">
                    <p className="text-[10px] font-black text-white/40 uppercase tracking-[0.2em] text-center">Tipo de combustible</p>
                    <div className="flex gap-2">
                       {['Gasolina', 'Diésel', 'Eléctrico'].map(f => (
                         <button key={f} onClick={() => handleVerdictFetch(f)} className="flex-1 py-3 px-2 rounded-xl bg-white/5 border border-white/10 hover:border-blue-500 hover:bg-blue-600/20 transition-all font-bold text-xs uppercase active:scale-95">{f}</button>
                       ))}
                    </div>
                  </motion.div>
                )}
              </div>
            )}

            {currentSlideIndex === 11 && (
              <div className="flex-1 flex flex-col justify-center space-y-8">
                {loading ? (
                  <div className="text-center space-y-4">
                    <motion.div animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: "linear" }} className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full mx-auto" />
                    <p className="text-white/50 font-bold uppercase tracking-widest text-xs">Calculando veredicto...</p>
                  </div>
                ) : verdict ? (
                  <motion.div initial={{ opacity: 0, scale: 0.9, y: 20 }} animate={{ opacity: 1, scale: 1, y: 0 }} className="space-y-6">
                    <div className="holographic-border p-6 rounded-3xl bg-black/40 backdrop-blur-xl border border-white/5 overflow-hidden relative group">
                       <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-transparent pointer-events-none" />
                       
                       <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/20 text-blue-400 text-[10px] font-black uppercase tracking-[0.2em] mb-4">
                         <Zap size={14} /> El Veredicto Final
                       </div>
                       
                       <h2 className="text-4xl font-black leading-tight tracking-tighter italic mb-4">
                         {userChoice.marca} {userChoice.modelo} <br />
                         <span className="text-blue-400">{verdict.verdict_title}</span>
                       </h2>
                       
                       <p className="text-lg text-white/80 leading-snug italic font-medium mb-6">
                         &quot;{verdict.verdict_text}&quot;
                       </p>

                       <div className="grid grid-cols-2 gap-4 pt-6 border-t border-white/10">
                         <div className="">
                            <p className="text-[10px] text-white/30 uppercase font-black">Precio Estimado</p>
                            <p className="text-2xl font-black font-mono text-green-400 italic">${verdict.avg_price_usd.toLocaleString()}</p>
                         </div>
                         <div className="text-right">
                            <p className="text-[10px] text-white/30 uppercase font-black">Cuota Mercado</p>
                            <p className="text-2xl font-black font-mono text-blue-400 italic">{verdict.market_share_percent < 0.1 ? '<0.1%' : verdict.market_share_percent.toFixed(2) + '%'}</p>
                         </div>
                       </div>
                    </div>

                    <div className="flex flex-col gap-3">
                      <Link href="/search" className="w-full py-4 bg-blue-600 hover:bg-blue-500 rounded-2xl flex items-center justify-center gap-2 font-black transition-all transform hover:scale-[1.02] shadow-xl shadow-blue-900/40 text-white">
                        <Search size={18} /> Explorar este modelo ahora
                      </Link>
                      <button onClick={() => setCurrentSlideIndex(0)} className="w-full py-2 text-center text-white/30 hover:text-white transition-all text-xs uppercase tracking-widest font-bold">Reiniciar historia</button>
                    </div>
                  </motion.div>
                ) : (
                  <div className="text-center">Error al procesar. Reintenta.</div>
                )}
              </div>
            )}
          </motion.div>
        </AnimatePresence>

        {/* Manual Navigation Overlay (Invisible) */}
        {!['brand-selection', 'model-selection', 'verdict'].includes(SLIDES[currentSlideIndex]) && (
           <div className="absolute inset-0 flex z-30 pointer-events-none">
              <div className="w-1/3 h-full pointer-events-auto cursor-w-resize" onClick={(e) => { e.stopPropagation(); prevSlide(); }} />
              <div className="flex-1 h-full pointer-events-auto cursor-e-resize" onClick={(e) => { e.stopPropagation(); nextSlide(); }} />
           </div>
        )}
      </div>

      <style jsx global>{`
        .custom-scrollbar::-webkit-scrollbar { width: 4px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: rgba(255, 255, 255, 0.05); }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.1); border-radius: 10px; }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(255, 255, 255, 0.2); }
      `}</style>
    </main>
  );
}
