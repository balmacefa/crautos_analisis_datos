"use client";

import React from 'react';
import { motion } from 'framer-motion';
import { Car, Sun, Moon } from 'lucide-react';
import { useTheme } from '@/context/ThemeContext';
import { cn } from '@/lib/utils';

export const Header = ({ className }) => {
  const { theme, toggleTheme } = useTheme();

  return (
    <header className={cn("pt-12 pb-8 text-center space-y-4", className)}>
      <div className="flex justify-between items-center mb-6">
        <motion.div 
          whileHover={{ scale: 1.1 }}
          className={cn(
            "w-10 h-10 rounded-full flex items-center justify-center glass transition-colors",
            theme === 'dark' ? 'text-cyan-400 border-cyan-500/30' : 'text-slate-800 border-slate-300'
          )}
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
        className={cn(
          "text-4xl font-extrabold tracking-tighter uppercase font-display leading-[0.9]",
          theme === 'dark' ? 'text-white' : 'text-slate-900'
        )}
      >
        EL FUTURO DEL <br />
        <span className={cn(
          theme === 'dark' 
            ? 'text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-purple-500 text-glow' 
            : 'text-cyan-600'
        )}>
          ANÁLISIS AUTOMOTRIZ
        </span>
      </motion.h1>
      
      <p className={cn(
        "text-sm font-medium tracking-tight px-8",
        theme === 'dark' ? 'text-slate-400' : 'text-slate-600'
      )}>
        Explora el mercado automotriz de Costa Rica con datos en tiempo real.
      </p>
    </header>
  );
};
