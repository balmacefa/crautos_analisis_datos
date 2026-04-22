"use client";
import React, { useState, useMemo, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  ArrowLeft, 
  ArrowRight, 
  ChevronRight, 
  Car, 
  TrendingUp, 
  MapPin, 
  Gauge, 
  Zap, 
  TrendingDown, 
  DollarSign, 
  Calendar,
  Layers,
  Fuel,
  Info
} from "lucide-react";
import Link from "next/link";
import useSWR from "swr";
import { useTheme } from "@/context/ThemeContext";
import { cn } from "@/lib/utils";
import { getApiBaseUrl, robustFetcher as fetcher } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Background } from "@/components/layout/Background";

export default function WrappedStory() {
  const { theme } = useTheme();
  const [currentSlide, setCurrentSlide] = useState(0);
  const [direction, setDirection] = useState(0);
  const baseUrl = getApiBaseUrl();

  // Data fetching for all slides
  const { data: summary } = useSWR(`${baseUrl}/api/insights/summary`, fetcher);
  const { data: brands = [] } = useSWR(`${baseUrl}/api/insights/brands`, fetcher);
  const { data: provinces = [] } = useSWR(`${baseUrl}/api/insights/provinces`, fetcher);
  const { data: fuelStats = [] } = useSWR(`${baseUrl}/api/insights/distribution/fuel`, fetcher);
  const { data: transStats = [] } = useSWR(`${baseUrl}/api/insights/distribution/transmission`, fetcher);
  const { data: yearStats = [] } = useSWR(`${baseUrl}/api/insights/years`, fetcher);
  const { data: curiosities } = useSWR(`${baseUrl}/api/insights/curiosities`, fetcher);
  const { data: opportunities = [] } = useSWR(`${baseUrl}/api/insights/opportunities`, fetcher);

  const slides = [
    // 0: Intro
    {
      type: "intro",
      title: "Tu Mercado, Un Resumen",
      subtitle: "2024 wrapped",
      content: (
        <div className="text-center space-y-8">
          <div className="relative inline-block">
             <div className="absolute -inset-4 bg-cyan-500/20 blur-3xl rounded-full" />
             <Car size={80} className="text-cyan-400 relative z-10 mx-auto" />
          </div>
          <div className="space-y-2">
            <h1 className="text-6xl md:text-8xl font-black italic tracking-tighter leading-none">CRAUTOS <span className="text-cyan-400">WRAPPED</span></h1>
            <p className="text-lg text-white/40 font-bold uppercase tracking-[0.3em] mt-4">Análisis del mercado automotriz en tiempo real</p>
          </div>
          <div className="pt-12">
            <Button size="lg" onClick={() => nextSlide()} className="group px-12 py-6 text-lg uppercase tracking-widest gap-4">
              Comenzar la historia <ArrowRight className="group-hover:translate-x-2 transition-transform" />
            </Button>
          </div>
        </div>
      )
    },
    // 1: Big Numbers
    {
       type: "stat",
       title: "La Magnitud",
       content: (
         <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
           <Card className="p-10 flex flex-col justify-center items-center text-center space-y-4" hover={false}>
              <p className="text-[10px] font-black uppercase tracking-[0.3em] text-white/30">Anuncios Analizados</p>
              <h2 className="text-7xl font-black italic text-cyan-400 tracking-tighter">{summary?.total_listings?.toLocaleString() || "..."}</h2>
              <p className="text-sm text-white/60">Unidades activas en el mercado hoy</p>
           </Card>
           <Card className="p-10 flex flex-col justify-center items-center text-center space-y-4 border-cyan-500/20" hover={false}>
              <p className="text-[10px] font-black uppercase tracking-[0.3em] text-white/30">Precio Promedio</p>
              <h2 className="text-7xl font-black italic text-green-400 tracking-tighter">${summary?.avg_price_usd?.toLocaleString() || "..."}</h2>
              <p className="text-sm text-white/60">Valor medio en dólares americanos</p>
           </Card>
         </div>
       )
    },
    // 2: Market Leaders
    {
      type: "list",
      title: "Los Reyes de la Calle",
      content: (
        <div className="space-y-6 w-full max-w-2xl mx-auto">
          <p className="text-white/40 text-sm mb-12 text-center uppercase tracking-widest font-bold">Marcas con mayor inventario</p>
          {brands.slice(0, 5).map((b, i) => (
            <Card key={i} className="p-4 flex items-center justify-between group" hover={true}>
              <div className="flex items-center gap-6">
                <span className="text-4xl font-black italic text-white/10 group-hover:text-cyan-400/20 transition-colors w-12">{i + 1}</span>
                <span className="text-2xl font-black tracking-tighter uppercase">{b.marca}</span>
              </div>
              <div className="text-right">
                <span className="text-xl font-bold text-cyan-400">{b.count.toLocaleString()}</span>
                <p className="text-[8px] font-black uppercase text-white/20 tracking-widest mt-1">unidades</p>
              </div>
            </Card>
          ))}
        </div>
      )
    },
    // 3: Geography
    {
      type: "stat",
      title: "¿Dónde están?",
      content: (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {provinces.slice(0, 4).map((p, i) => (
            <Card key={i} className="p-8 text-center space-y-4" hover={false}>
              <div className="w-12 h-12 bg-white/5 rounded-2xl flex items-center justify-center mx-auto">
                <MapPin size={20} className={i === 0 ? "text-cyan-400" : "text-white/40"} />
              </div>
              <div>
                <h3 className="text-xl font-black tracking-tighter truncate uppercase">{p.provincia}</h3>
                <p className="text-sm font-bold text-cyan-400">{((p.count / (summary?.total_listings || 1)) * 100).toFixed(1)}%</p>
              </div>
            </Card>
          ))}
        </div>
      )
    },
    // 4: Market Curiosities (Extreme Prices)
    {
      type: "stat",
      title: "Extremos",
      content: (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
           <Card className="p-8 space-y-6 bg-red-500/5 border-red-500/10" hover={false}>
              <div className="flex items-center gap-3 text-red-400 font-black text-[10px] uppercase tracking-widest">
                <TrendingUp size={16} /> Lo más exclusivo
              </div>
              <div className="space-y-2">
                <h3 className="text-3xl font-black italic tracking-tighter leading-none">{curiosities?.luxury_leaders?.[0]?.marca || "Cargando..."}</h3>
                <p className="text-white/40 text-xs uppercase font-bold">{curiosities?.luxury_leaders?.[0]?.modelo}</p>
              </div>
              <p className="text-5xl font-black font-mono text-white tracking-tighter">${curiosities?.luxury_leaders?.[0]?.precio_usd?.toLocaleString()}</p>
           </Card>
           <Card className="p-8 space-y-6 bg-green-500/5 border-green-500/10" hover={false}>
              <div className="flex items-center gap-3 text-green-400 font-black text-[10px] uppercase tracking-widest">
                <TrendingDown size={16} /> La Oportunidad
              </div>
              <div className="space-y-2">
                <h3 className="text-3xl font-black italic tracking-tighter leading-none">{curiosities?.value_leader?.marca || "Cargando..."}</h3>
                <p className="text-white/40 text-xs uppercase font-bold">{curiosities?.value_leader?.modelo}</p>
              </div>
              <p className="text-5xl font-black font-mono text-white tracking-tighter">${curiosities?.value_leader?.precio_usd?.toLocaleString()}</p>
           </Card>
        </div>
      )
    },
    // 5: Fuel Stats
    {
      type: "viz",
      title: "El Alma del Motor",
      content: (
        <div className="space-y-12 max-w-xl mx-auto w-full">
           {fuelStats.slice(0, 4).map((f, i) => (
             <div key={i} className="space-y-3">
               <div className="flex justify-between items-end">
                 <span className="text-lg font-black uppercase italic tracking-tighter flex items-center gap-2">
                   <Fuel size={14} className="text-cyan-400" /> {f.combustible}
                 </span>
                 <span className="text-white/40 font-mono text-xs">{f.count.toLocaleString()} unid.</span>
               </div>
               <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden">
                 <motion.div 
                   initial={{ width: 0 }}
                   animate={{ width: `${(f.count / (summary?.total_listings || 1)) * 100}%` }}
                   transition={{ duration: 1.5, delay: i * 0.2 }}
                   className="h-full bg-cyan-400"
                 />
               </div>
             </div>
           ))}
        </div>
      )
    },
    // 6: Transmissions
    {
      type: "viz",
      title: "Control de Potencia",
      content: (
        <div className="grid grid-cols-2 gap-8 max-w-2xl mx-auto w-full">
           {transStats.map((t, i) => (
             <Card key={i} className="p-10 text-center space-y-6" hover={false}>
               <div className="relative inline-flex items-center justify-center">
                  <Zap size={40} className={i === 0 ? "text-cyan-400" : "text-white/20"} />
                  <div className={`absolute -inset-4 rounded-full blur-xl ${i === 0 ? "bg-cyan-500/10" : "bg-transparent"}`} />
               </div>
               <div>
                 <h4 className="text-4xl font-black italic tracking-tighter uppercase">{t.transmisión}</h4>
                 <p className="text-white/40 font-bold uppercase tracking-widest text-[10px] mt-2">{((t.count / (summary?.total_listings || 1)) * 100).toFixed(0)}% del mercado</p>
               </div>
             </Card>
           ))}
        </div>
      )
    },
    // 7: Years Evolution
    {
      type: "chart",
      title: "El Paso del Tiempo",
      content: (
        <div className="w-full h-64 flex items-end justify-between gap-2 px-4">
           {yearStats.slice(-10).map((y, i) => (
             <div key={i} className="flex-1 flex flex-col items-center gap-3">
               <motion.div 
                 initial={{ height: 0 }}
                 animate={{ height: `${(y.count / Math.max(...yearStats.map(x => x.count))) * 100}%` }}
                 className="w-full bg-white/10 rounded-t-lg hover:bg-cyan-400 transition-colors relative group"
               >
                 <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-zinc-800 text-[8px] font-bold px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity">
                   {y.count}
                 </div>
               </motion.div>
               <span className="text-[10px] font-black text-white/20 rotate-[-45deg] whitespace-nowrap">{y.año}</span>
             </div>
           ))}
        </div>
      )
    },
    // 8: Verdict
    {
      type: "verdict",
      title: "El Veredicto",
      content: (
        <Card className="p-12 space-y-10 text-center max-w-2xl mx-auto border-cyan-500/30" hover={false}>
           <div className="w-16 h-16 bg-cyan-600 rounded-full flex items-center justify-center mx-auto shadow-[0_0_50px_rgba(8,145,178,0.3)]">
             <Info size={32} />
           </div>
           <div className="space-y-4">
             <h3 className="text-4xl font-black italic tracking-tighter uppercase">Análisis Final 2024</h3>
             <p className="text-lg text-white/60 leading-relaxed italic">
               "{summary?.verdict || "El mercado costarricense muestra una fuerte resiliencia con un inventario diversificado, destacando el dominio de marcas tradicionales japonesas mientras los modelos eléctricos ganan tracción significativa."}"
             </p>
           </div>
           <div className="pt-6 grid grid-cols-2 gap-4">
              <div className="p-4 bg-white/5 rounded-2xl">
                <p className="text-[8px] font-black text-white/20 uppercase tracking-widest">Mejor momento</p>
                <p className="font-bold text-cyan-400">Ahora</p>
              </div>
              <div className="p-4 bg-white/5 rounded-2xl">
                <p className="text-[8px] font-black text-white/20 uppercase tracking-widest">Confianza</p>
                <p className="font-bold text-cyan-400">Alta</p>
              </div>
           </div>
        </Card>
      )
    },
    // 9: Outro
    {
      type: "outro",
      title: "Sé el Experto",
      content: (
        <div className="text-center space-y-12">
          <div className="space-y-4">
            <h2 className="text-5xl font-black italic tracking-tighter italic">¿LISTO PARA TU PRÓXIMA AVENTURA?</h2>
            <p className="text-white/40 font-bold uppercase tracking-tighter">Explora cada unidad en detalle con nuestro potente buscador dinámico.</p>
          </div>
          <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
            <Link href="/search">
              <Button size="lg" variant="primary" className="px-16 py-8 text-xl font-black italic uppercase tracking-[0.2em] gap-4">
                Ir al explorador <ChevronRight />
              </Button>
            </Link>
          </motion.div>
        </div>
      )
    }
  ];

  const nextSlide = () => {
    if (currentSlide < slides.length - 1) {
      setDirection(1);
      setCurrentSlide(prev => prev + 1);
    }
  };

  const prevSlide = () => {
    if (currentSlide > 0) {
      setDirection(-1);
      setCurrentSlide(prev => prev - 1);
    }
  };

  const currentData = slides[currentSlide];

  return (
    <main className="h-screen w-full relative overflow-hidden bg-zinc-950 text-white font-sans selection:bg-cyan-500 selection:text-white">
      <Background />

      {/* Static Header Nav */}
      <nav className="absolute top-0 left-0 right-0 z-50 p-8 flex justify-between items-center pointer-events-none">
        <div className="flex items-center gap-4 pointer-events-auto">
          <Link href="/" className="p-3 bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl hover:bg-white/10 transition-colors">
            <ArrowLeft size={20} />
          </Link>
          <div>
            <h3 className="font-black italic tracking-tighter leading-none text-xl">Crautos<span className="text-cyan-400">Analítica</span></h3>
            <p className="text-[8px] font-black uppercase text-white/40 tracking-widest mt-1">Tour Interactivo 1.0</p>
          </div>
        </div>
        <div className="hidden md:flex gap-4 pointer-events-auto">
          {slides.map((_, i) => (
            <div 
              key={i} 
              className={cn(
                "h-1 px-3 rounded-full transition-all duration-500",
                i === currentSlide ? "bg-cyan-400 w-12" : i < currentSlide ? "bg-white/40" : "bg-white/10"
              )}
            />
          ))}
        </div>
      </nav>

      {/* Kinetic Background Elements */}
      <div className="absolute inset-0 pointer-events-none opacity-20 overflow-hidden">
        <motion.div animate={{ rotate: 360 }} transition={{ duration: 60, repeat: Infinity, ease: 'linear' }} className="absolute -top-[20%] -left-[10%] opacity-30">
          <Layers size={800} className="text-cyan-500/10" />
        </motion.div>
      </div>

      <div className="h-full w-full flex items-center justify-center relative">
        <AnimatePresence mode="wait" custom={direction}>
          <motion.div
            key={currentSlide}
            custom={direction}
            initial={{ opacity: 0, x: direction * 100, scale: 0.9 }}
            animate={{ opacity: 1, x: 0, scale: 1 }}
            exit={{ opacity: 0, x: -direction * 100, scale: 1.1 }}
            transition={{ type: 'spring', damping: 25, stiffness: 120 }}
            className="w-full max-w-6xl px-8 relative z-10"
          >
            <div className="mb-12 text-center">
               <motion.p 
                 initial={{ opacity: 0, y: 20 }}
                 animate={{ opacity: 1, y: 0 }}
                 className="text-[10px] font-black uppercase tracking-[0.4em] text-cyan-400 mb-2"
               >
                 {currentSlide + 1} / {slides.length}
               </motion.p>
               <motion.h2 
                 initial={{ opacity: 0, y: 10 }}
                 animate={{ opacity: 1, y: 0 }}
                 className="text-5xl md:text-7xl font-black italic tracking-tighter leading-none"
               >
                 {currentData.title}
               </motion.h2>
            </div>
            
            <div className="min-h-[40vh] flex items-center justify-center">
              {currentData.content}
            </div>
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Navigation Controls */}
      <div className="absolute bottom-12 left-1/2 -translate-x-1/2 z-50 flex items-center gap-12 bg-black/40 backdrop-blur-3xl px-8 py-5 rounded-[2.5rem] border border-white/10 shadow-2xl">
        <button 
          onClick={prevSlide}
          disabled={currentSlide === 0}
          className="p-3 text-white/40 hover:text-white disabled:opacity-20 transition-colors"
        >
          <ArrowLeft size={24} />
        </button>
        <div className="h-8 w-px bg-white/10" />
        <button 
          onClick={nextSlide}
          disabled={currentSlide === slides.length - 1}
          className="p-3 group text-white/40 hover:text-cyan-400 disabled:opacity-20 transition-all"
        >
          <ArrowRight size={24} className="group-hover:translate-x-1 transition-transform" />
        </button>
      </div>

      {/* Ambient noise / FX */}
      <div className="absolute bottom-8 right-8 pointer-events-none">
        <div className="flex items-center gap-3">
          <div className="w-2 h-2 bg-cyan-400 rounded-full animate-pulse shadow-[0_0_15px_rgba(34,211,238,0.8)]" />
          <span className="text-[10px] font-black text-white/20 uppercase tracking-[0.2em] font-mono">Real-time Node</span>
        </div>
      </div>
    </main>
  );
}
