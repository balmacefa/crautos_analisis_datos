"use client";

import React from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

const Button = React.forwardRef(({ 
  className, 
  variant = 'primary', 
  size = 'md', 
  children, 
  ...props 
}, ref) => {
  const variants = {
    primary: 'bg-gradient-to-r from-cyan-600 to-indigo-700 text-white shadow-[0_8px_20px_-5px_rgba(6,182,212,0.4)]',
    secondary: 'bg-white/5 border border-white/10 text-white hover:bg-white/10',
    outline: 'bg-transparent border border-cyan-500/50 text-cyan-400 hover:bg-cyan-500/10',
    ghost: 'bg-transparent text-slate-400 hover:text-white hover:bg-white/5',
    emerald: 'bg-gradient-to-r from-emerald-600 to-teal-700 text-white shadow-[0_8px_20px_-5px_rgba(16,185,129,0.4)]',
    purple: 'bg-gradient-to-r from-purple-600 to-indigo-700 text-white shadow-[0_8px_20px_-5px_rgba(139,92,246,0.4)]',
  };

  const sizes = {
    sm: 'px-4 py-2 text-[10px]',
    md: 'px-6 py-3 text-sm',
    lg: 'px-8 py-4 text-base',
  };

  return (
    <motion.button
      ref={ref}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      className={cn(
        'inline-flex items-center justify-center rounded-2xl font-bold tracking-wide transition-all focus:outline-none focus:ring-2 focus:ring-cyan-500 disabled:opacity-50 disabled:cursor-not-allowed',
        variants[variant],
        sizes[size],
        className
      )}
      {...props}
    >
      {children}
    </motion.button>
  );
});

Button.displayName = 'Button';

export { Button };
