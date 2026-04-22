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
  Settings2
} from 'lucide-react';
import Link from 'next/link';
import { cn } from '@/lib/utils';
import confetti from 'canvas-confetti';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { useTheme } from '@/context/ThemeContext';

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

export default function WrappedStory() {
  const { theme: appTheme } = useTheme();
  const [currentSlideIndex, setCurrentSlideIndex] = useState(0);
  const [direction, setDirection] = useState(1);
  const [globalStats, setGlobalStats] = useState(null);
  const [curiosities, setCuriosities] = useState(null);
  const [fuelStats, setFuelStats] = useState([]);
  const [brands, setBrands] = useState([]);
  const [isPaused, setIsPaused] = useState(false);

  useEffect(() => {
    async function fetchData() {
      const baseUrl = getApiBaseUrl();
      try {
        const [summaryData, curiosData, brandsData, fuelData] = await Promise.all([
          fetcher(`${baseUrl}/api/insights/summary`),
          fetcher(`${baseUrl}/api/insights/curiosities`),
          fetcher(`${baseUrl}/api/insights/brands`),
          fetcher(`${baseUrl}/api/insights/distribution/fuel`),
        ]);
        
        if (summaryData) setGlobalStats(summaryData);
        if (curiosData) setCuriosities(curiosData);
        if (brandsData) setBrands(brandsData);
        if (fuelData) setFuelStats(fuelData);
      } catch (error) {
        console.error("Error fetching data:", error);
      }
    }
    fetchData();
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
    >
      <div className="absolute inset-0 z-0 overflow-hidden pointer-events-none opacity-20">
         <motion.div animate={{ y: [0, -20, 0] }} transition={{ duration: 5, repeat: Infinity }} className="absolute top-[10%] left-[5%]"><Key size={100} /></motion.div>
         <motion.div animate={{ y: [0, 20, 0] }} transition={{ duration: 6, repeat: Infinity }} className="absolute bottom-[20%] right-[10%]"><Navigation size={120} /></motion.div>
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

            {/* Other slides follow similar pattern... but simplified for this refactor demo */}
            {currentSlideIndex > 1 && (
               <Card className="flex-1 flex flex-col justify-center items-center text-center gap-4" hover={false}>
                  <p className="text-white/40 uppercase font-black tracking-widest text-xs">Sección en Refactorización</p>
                  <Button variant="secondary" onClick={() => setCurrentSlideIndex(0)}>Reiniciar</Button>
               </Card>
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
