"use client";

import React from 'react';
import { motion } from 'framer-motion';
import { useTheme } from '@/context/ThemeContext';

export const Background = ({ variant = 'default' }) => {
  const { theme } = useTheme();

  return (
    <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
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

      {/* Decorative Circuits */}
      <svg className="absolute top-0 right-0 w-full h-full opacity-[0.05] pointer-events-none" viewBox="0 0 1000 1000">
        <path d="M0,100 Q250,50 500,100 T1000,50" fill="none" stroke="currentColor" strokeWidth="1" />
        <path d="M0,300 Q250,250 500,300 T1000,250" fill="none" stroke="currentColor" strokeWidth="1" />
        <path d="M0,500 L1000,500" fill="none" stroke="currentColor" strokeWidth="0.5" strokeDasharray="10 10" />
      </svg>
    </div>
  );
};
