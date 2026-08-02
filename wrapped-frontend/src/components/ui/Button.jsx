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
    secondary: 'bg-slate-100 border border-slate-200 text-slate-700 hover:bg-slate-200 dark:bg-white/5 dark:border-white/10 dark:text-white dark:hover:bg-white/10',
    outline: 'bg-transparent border border-cyan-500/50 text-cyan-600 hover:bg-cyan-500/10 dark:text-cyan-400',
    ghost: 'bg-transparent text-slate-500 hover:text-slate-900 hover:bg-slate-100 dark:text-slate-400 dark:hover:text-white dark:hover:bg-white/5',
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
