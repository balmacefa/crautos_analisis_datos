"use client"
import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  Car, 
  Search, 
  BarChart3, 
  Compass, 
  Home, 
  LayoutDashboard, 
  ChevronRight,
  Sun,
  Moon,
  Sparkles,
  Zap,
  Globe
} from 'lucide-react';

// --- Components ---

const Badge = ({ children, className = "" }) => (
  <span className={`px-2 py-0.5 text-[10px] font-bold tracking-wider uppercase rounded-full bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 ${className}`}>
    {children}
  </span>
);

const GlassCard = ({ children, className = "", delay = 0 }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.6, delay }}
    className={`relative overflow-hidden rounded-3xl p-6 transition-all duration-300 ${className}`}
  >
    {children}
  </motion.div>
);

const NavItem = ({ icon: Icon, label, active, href }) => (
  <Link 
    href={href}
    className={`flex flex-col items-center gap-1 transition-all duration-300 ${active ? 'text-cyan-500' : 'text-slate-500 hover:text-slate-300'}`}
  >
    <div className={`p-2 rounded-xl transition-all duration-300 ${active ? 'bg-cyan-500/10' : ''}`}>
      <Icon size={24} className={active ? 'drop-shadow-[0_0_8px_rgba(6,182,212,0.6)]' : ''} />
    </div>
    <span className="text-[10px] font-medium tracking-wide uppercase">{label}</span>
  </Link>
);

// --- Main App ---

export default function App() {
  const [theme, setTheme] = useState('dark');
  const pathname = usePathname();

  // Determine active tab based on route
  const getActiveTab = () => {
    if (pathname === '/tour') return 'Tour';
    if (pathname === '/search') return 'Explorer';
    if (pathname === '/insights') return 'Insights';
    return 'Inicio';
  };

  const activeTab = getActiveTab();

  // Toggle theme colors
  const toggleTheme = () => setTheme(prev => prev === 'dark' ? 'light' : 'dark');

  // Body theme class
  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark');
    if (theme === 'light') {
      document.body.className = 'bg-slate-50 text-slate-900 transition-colors duration-500';
    } else {
      document.body.className = 'bg-slate-950 text-slate-100 transition-colors duration-500';
    }
  }, [theme]);

  // Background patterns
  const Background = () => (
    <div className="fixed inset-0 -z-10 overflow-hidden">
      {/* Animated Gradients */}
      <motion.div 
        animate={{ 
          scale: [1, 1.2, 1],
          opacity: [0.3, 0.5, 0.3],
          x: [0, 50, 0],
          y: [0, 30, 0]
        }}
        transition={{ duration: 15, repeat: Infinity, ease: 'linear' }}
        className="absolute -top-[10%] -left-[10%] w-[60%] h-[60%] bg-cyan-500/10 blur-[120px] rounded-full"
      />
      <motion.div 
        animate={{ 
          scale: [1, 1.3, 1],
          opacity: [0.2, 0.4, 0.2],
          x: [0, -40, 0],
          y: [0, -50, 0]
        }}
        transition={{ duration: 20, repeat: Infinity, ease: 'linear' }}
        className="absolute bottom-0 right-0 w-[70%] h-[70%] bg-purple-500/10 blur-[150px] rounded-full"
      />
      
      {/* Grid Pattern */}
      <div className={`absolute inset-0 opacity-[0.03] ${theme === 'dark' ? 'invert-0' : 'invert'}`}
        style={{ backgroundImage: 'radial-gradient(circle, #fff 1px, transparent 1px)', backgroundSize: '32px 32px' }}
      />

      {/* Decorative Circuits (Simulated) */}
      <svg className="absolute top-0 right-0 w-full h-full opacity-[0.05] pointer-events-none" viewBox="0 0 1000 1000">
        <path d="M0,100 Q250,50 500,100 T1000,50" fill="none" stroke="currentColor" strokeWidth="1" />
        <path d="M0,300 Q250,250 500,300 T1000,250" fill="none" stroke="currentColor" strokeWidth="1" />
        <path d="M0,500 L1000,500" fill="none" stroke="currentColor" strokeWidth="0.5" strokeDasharray="10 10" />
      </svg>
    </div>
  );

  return (
    <div className="min-h-screen pb-32 max-w-md mx-auto relative px-6 overflow-x-hidden">
      <Background />

      {/* Header */}
      <header className="pt-12 pb-8 text-center space-y-4">
        <div className="flex justify-between items-center mb-6">
          <motion.div 
            whileHover={{ scale: 1.1 }}
            className={`w-10 h-10 rounded-full flex items-center justify-center glass ${theme === 'dark' ? 'text-cyan-400 border-cyan-500/30' : 'text-slate-800 border-slate-300'}`}
          >
            <Car size={20} />
          </motion.div>
          <button 
            onClick={toggleTheme}
            className="p-2 rounded-full glass hover:scale-110 transition-transform"
          >
            {theme === 'dark' ? <Sun size={20} className="text-amber-400" /> : <Moon size={20} className="text-slate-700" />}
          </button>
        </div>

        <motion.h1 
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8 }}
          className={`text-4xl font-extrabold tracking-tighter uppercase font-display leading-[0.9] ${theme === 'dark' ? 'text-white' : 'text-slate-900'}`}
        >
          EL FUTURO DEL <br />
          <span className={theme === 'dark' ? 'text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-purple-500 text-glow' : 'text-cyan-600'}>
            ANÁLISIS AUTOMOTRIZ
          </span>
        </motion.h1>
        
        <p className={`text-sm font-medium tracking-tight px-8 ${theme === 'dark' ? 'text-slate-400' : 'text-slate-600'}`}>
          Explora el mercado automotriz de Costa Rica con datos en tiempo real.
        </p>
      </header>

      {/* Main Content */}
      <main className="space-y-6">
        
        {/* Card 1: Interactive Tour */}
        <Link href="/tour" className="block focus:outline-none focus:ring-2 focus:ring-cyan-500 rounded-3xl">
          <GlassCard 
            delay={0.1} 
            className={theme === 'dark' ? 'glass-dark hover:border-cyan-500/40 group cursor-pointer' : 'bg-white shadow-xl shadow-slate-200 border-slate-100 group cursor-pointer'}
          >
            {/* Card background image/effect */}
            <div className="absolute top-0 right-0 w-2/3 h-full overflow-hidden pointer-events-none opacity-40">
               <div className="absolute inset-0 bg-gradient-to-l from-transparent via-transparent to-transparent z-10" />
               <div className="absolute top-0 right-0 w-full h-full transform translate-x-1/4 skew-x-12 bg-gradient-to-r from-cyan-500/20 to-purple-500/20 blur-2xl flex items-center">
                  {/* Faint Highway Image Overlay */}
                  <img src="/images/tour-bg.png" alt="Tour Background" className="absolute mix-blend-screen opacity-50 object-cover object-center scale-150 rounded-full" />
               </div>
               {/* Simulated light trails */}
               <motion.div 
                 animate={{ x: [-100, 200] }}
                 transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
                 className="absolute top-1/4 right-0 w-32 h-[1px] bg-cyan-400 shadow-[0_0_15px_#22d3ee] rotate-[-5deg]" 
               />
               <motion.div 
                 animate={{ x: [200, -100] }}
                 transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }}
                 className="absolute top-1/2 right-0 w-48 h-[1px] bg-purple-400 shadow-[0_0_15px_#a855f7] rotate-[-5deg]" 
               />
            </div>

            <div className="relative z-10 space-y-4 pr-12">
              <div className="flex items-center gap-3">
                <div className={`p-2 rounded-lg ${theme === 'dark' ? 'bg-cyan-500/10 text-cyan-400' : 'bg-cyan-50 text-cyan-600'}`}>
                  <Compass size={24} />
                </div>
                <h2 className={`text-xl font-bold font-display ${theme === 'dark' ? 'text-white' : 'text-slate-900'}`}>Interactive Tour</h2>
              </div>
              
              <p className={`text-sm leading-relaxed ${theme === 'dark' ? 'text-slate-400' : 'text-slate-600'}`}>
                Descubre tu historia con el mercado. Un viaje inmersivo, estilo <span className="font-semibold italic">Spotify Wrapped</span>, por las tendencias automotrices.
              </p>

              <div 
                className={`inline-flex items-center gap-2 py-3 px-6 rounded-2xl text-sm font-bold tracking-wide transition-all group-hover:scale-[1.02] active:scale-[0.98] ${
                  theme === 'dark' 
                  ? 'bg-gradient-to-r from-cyan-600 to-indigo-700 text-white shadow-[0_8px_20px_-5px_rgba(6,182,212,0.4)]' 
                  : 'bg-slate-900 text-white'
                }`}
              >
                COMENZAR EL VIAJE <ChevronRight size={16} className="group-hover:translate-x-1 transition-transform" />
              </div>
            </div>
          </GlassCard>
        </Link>

        {/* Card 2: Market Explorer */}
        <Link href="/search" className="block focus:outline-none focus:ring-2 focus:ring-purple-500 rounded-3xl">
          <GlassCard 
            delay={0.2} 
            className={theme === 'dark' ? 'glass-dark hover:border-purple-500/40 group cursor-pointer' : 'bg-white shadow-xl shadow-slate-200 border-slate-100 group cursor-pointer'}
          >
            <div className="absolute top-0 right-0 w-2/3 h-full overflow-hidden pointer-events-none opacity-40">
              <div className="absolute -top-12 -right-12 w-48 h-48 bg-purple-500/5 blur-3xl rounded-full" />
              <div className="absolute top-0 right-0 w-full h-full transform translate-x-1/4 skew-x-12 bg-gradient-to-r from-purple-500/20 to-indigo-500/20 blur-2xl flex items-center">
                  <img src="/images/search-bg.png" alt="Search Background" className="absolute mix-blend-screen opacity-50 object-cover object-center scale-150 rounded-full" />
              </div>
            </div>
            
            <div className="relative z-10 space-y-4">
              <div className="flex items-center gap-3">
                <div className={`p-2 rounded-lg ${theme === 'dark' ? 'bg-purple-500/10 text-purple-400' : 'bg-purple-50 text-purple-600'}`}>
                  <Search size={24} />
                </div>
                <h2 className={`text-xl font-bold font-display ${theme === 'dark' ? 'text-white' : 'text-slate-900'}`}>Market Explorer</h2>
              </div>

              <div className="flex flex-wrap gap-2 mb-2">
                <Badge>Top Ventas</Badge>
                <Badge className="!bg-purple-500/20 !text-purple-400 !border-purple-500/30">Híbridos</Badge>
                <Badge className="!bg-amber-500/20 !text-amber-400 !border-amber-500/30">ELÉCTRICO</Badge>
              </div>
              
              <p className={`text-sm leading-relaxed ${theme === 'dark' ? 'text-slate-400' : 'text-slate-600'}`}>
                Busca y compara miles de vehículos con filtros avanzados y sugerencias potenciadas por <span className="font-semibold text-purple-400">inteligencia artificial</span>.
              </p>

              {/* Simulated Search UI Element */}
              <div className={`mt-2 p-3 rounded-xl flex items-center gap-3 w-[110%] -ml-[5%] lg:w-auto lg:ml-0 relative ${theme === 'dark' ? 'bg-white/5 border border-white/10' : 'bg-slate-50 border border-slate-200'}`}>
                <Sparkles size={14} className="text-purple-400" />
                <div className="flex-1 space-y-1">
                  <div className={`h-1.5 w-2/3 rounded-full ${theme === 'dark' ? 'bg-white/20' : 'bg-slate-300'}`} />
                  <div className={`h-1.5 w-1/2 rounded-full opacity-50 ${theme === 'dark' ? 'bg-white/20' : 'bg-slate-300'}`} />
                </div>
                <Badge className="text-[8px] shrink-0">AI suggest</Badge>
              </div>

              <div 
                className={`inline-flex items-center gap-2 py-3 px-6 rounded-2xl text-sm font-bold tracking-wide transition-all group-hover:scale-[1.02] active:scale-[0.98] mt-2 ${
                  theme === 'dark' 
                  ? 'bg-gradient-to-r from-purple-600 to-indigo-700 text-white shadow-[0_8px_20px_-5px_rgba(139,92,246,0.4)]' 
                  : 'bg-purple-600 text-white'
                }`}
              >
                EXPLORAR MERCADO <ChevronRight size={16} className="group-hover:translate-x-1 transition-transform" />
              </div>
            </div>
          </GlassCard>
        </Link>

        {/* Card 3: Insights Dashboard */}
        <Link href="/insights" className="block focus:outline-none focus:ring-2 focus:ring-emerald-500 rounded-3xl">
          <GlassCard 
            delay={0.3} 
            className={theme === 'dark' ? 'glass-dark hover:border-emerald-500/40 group cursor-pointer' : 'bg-white shadow-xl shadow-slate-200 border-slate-100 group cursor-pointer'}
          >
            {/* Simulated Map Background */}
            <div className="absolute bottom-0 right-0 w-2/3 h-full overflow-hidden pointer-events-none opacity-30">
               <div className="absolute top-0 right-0 w-full h-full bg-gradient-to-r from-emerald-500/10 to-transparent blur-xl flex items-center opacity-60">
                  <img src="/images/insights-bg.png" alt="Insights Background" className="absolute mix-blend-screen opacity-50 object-cover object-center scale-150 rounded-full right-[-50px]" />
               </div>
              <svg viewBox="0 0 100 100" className={`absolute bottom-0 right-0 w-full h-full ${theme === 'dark' ? 'text-emerald-500' : 'text-emerald-700'}`}>
                 <path d="M30,20 Q40,10 60,30 T80,50 L90,80 L50,90 L20,70 Z" fill="currentColor" fillOpacity="0.2" />
                 <circle cx="50" cy="50" r="5" fill="currentColor" fillOpacity="0.8">
                   <animate attributeName="r" values="5;8;5" dur="2s" repeatCount="indefinite" />
                   <animate attributeName="opacity" values="0.8;0.4;0.8" dur="2s" repeatCount="indefinite" />
                 </circle>
              </svg>
            </div>

            <div className="relative z-10 space-y-4">
              <div className="flex items-center gap-3">
                <div className={`p-2 rounded-lg ${theme === 'dark' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-emerald-50 text-emerald-600'}`}>
                  <BarChart3 size={24} />
                </div>
                <h2 className={`text-xl font-bold font-display ${theme === 'dark' ? 'text-white' : 'text-slate-900'}`}>Insights Dashboard</h2>
              </div>
              
              <p className={`text-sm leading-relaxed pr-10 ${theme === 'dark' ? 'text-slate-400' : 'text-slate-600'}`}>
                Métricas globales, líderes del mercado, distribución geográfica y estadísticas profundas actualizadas en tiempo real.
              </p>

              {/* Simulated Chart */}
              <div className="h-12 flex items-end gap-1 px-1 w-3/4">
                {[40, 70, 45, 90, 65, 80, 55, 95].map((val, i) => (
                  <motion.div 
                    key={i}
                    initial={{ height: 0 }}
                    animate={{ height: `${val}%` }}
                    transition={{ duration: 1, delay: 0.5 + (i * 0.1) }}
                    className={`flex-1 rounded-t-[2px] ${theme === 'dark' ? 'bg-emerald-500/40' : 'bg-emerald-600/30'}`}
                  />
                ))}
              </div>

              <div 
                className={`inline-flex items-center gap-2 py-3 px-6 rounded-2xl text-sm font-bold tracking-wide transition-all group-hover:scale-[1.02] active:scale-[0.98] mt-2 ${
                  theme === 'dark' 
                  ? 'bg-gradient-to-r from-emerald-600 to-cyan-700 text-white shadow-[0_8px_20px_-5px_rgba(16,185,129,0.4)]' 
                  : 'bg-emerald-600 text-white'
                }`}
              >
                VER ESTADÍSTICAS <ChevronRight size={16} className="group-hover:translate-x-1 transition-transform" />
              </div>
            </div>
          </GlassCard>
        </Link>

      </main>

      {/* Bottom Navigation */}
      <nav className={`fixed bottom-6 left-1/2 -translate-x-1/2 w-[calc(100%-48px)] max-w-md p-4 rounded-[32px] glass z-50 flex justify-between items-center px-8 shadow-2xl overflow-hidden ${
        theme === 'dark' ? 'glass-dark' : 'bg-white/90 border-slate-200'
      }`}>
        {/* Navigation Indicator Background */}
        <div className="absolute inset-0 bg-gradient-to-t from-white/5 to-transparent pointer-events-none" />
        
        <NavItem 
          icon={Home} 
          label="Inicio" 
          active={activeTab === 'Inicio'} 
          href="/"
        />
        <NavItem 
          icon={Compass} 
          label="Tour" 
          active={activeTab === 'Tour'} 
          href="/tour"
        />
        <NavItem 
          icon={Search} 
          label="Explorer" 
          active={activeTab === 'Explorer'} 
          href="/search"
        />
        <NavItem 
          icon={LayoutDashboard} 
          label="Insights" 
          active={activeTab === 'Insights'} 
          href="/insights"
        />
      </nav>

      {/* Footer Meta */}
      <footer className="mt-12 text-center pb-8 opacity-40 text-[10px] font-mono tracking-widest uppercase">
        <div className="flex items-center justify-center gap-4">
          <div className="flex items-center gap-1"><Zap size={10} className="text-cyan-400" /> v.4.2.0</div>
          <div className="flex items-center gap-1"><Globe size={10} className="text-purple-400" /> COSTA RICA</div>
          <div>EST. 2026</div>
        </div>
      </footer>
    </div>
  );
}
